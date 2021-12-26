import graphene
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django_plus.types import ModelType
from graphql_jwt.exceptions import PermissionDenied

from apps.meet_plan.models import MeetPlan, TermDate
from apps.pku_auth.meta import PKTypeMixin, AbstractMeta
from apps.user.schema import UserType


class TermDateType(ModelType):
    class Meta(AbstractMeta):
        model = TermDate
        fields = ["start_date"]
        allow_unauthenticated = True


class MeetPlanType(PKTypeMixin, ModelType):
    class Meta(AbstractMeta):
        model = MeetPlan
        fields = [
            "teacher",
            "place",
            "start_time",
            "duration",
            "t_message",
            # "available",
            # "student",
            # "s_message",
            # "complete",
        ]
        filter_fields = {
            "teacher__id": ["exact", "in"],
            "start_time": ["lt", "gt"],
            "duration": ["exact", "in", "gte", "lte"],
            # TODO: make student__pku_id filter only for admin user to protect privacy
            "student__pku_id": ["exact", "contains", "startswith"],
            "complete": ["exact"],
        }

    available = graphene.Boolean()

    @staticmethod
    def resolve_available(parent, info):
        return parent.is_available()

    student = graphene.Field(UserType)

    @staticmethod
    def resolve_student(parent, info):
        user = info.context.user
        if user.is_admin:
            return parent.student
        if user.is_teacher and user.id == parent.teacher_id:
            return parent.student
        if user.id == parent.student_id:
            return parent.student
        raise PermissionDenied

    s_message = graphene.String()

    @staticmethod
    def resolve_s_message(parent, info):
        user = info.context.user
        if user.is_admin:
            return parent.s_message
        if user.is_teacher and user.id == parent.teacher_id:
            return parent.s_message
        if user.id == parent.student_id:
            return parent.s_message
        raise PermissionDenied

    complete = graphene.Boolean()

    @staticmethod
    def resolve_complete(parent, info):
        user = info.context.user
        if user.is_admin:
            return parent.complete
        if user.is_teacher and user.id == parent.teacher_id:
            return parent.complete
        if user.id == parent.student_id:
            return parent.complete
        raise PermissionDenied

    @classmethod
    def get_queryset(cls, qs, info):
        qs = super().get_queryset(qs, info)
        user = info.context.user
        if user.is_admin:
            return qs
        if user.is_teacher:
            return qs.filter(teacher_id=user.id)
        return qs


class Query(graphene.ObjectType):
    term_date = graphene.Field(TermDateType)

    @staticmethod
    def resolve_term_date(parent, info):
        return TermDate.objects.last()

    meet_plan = relay.Node.Field(MeetPlanType)
    meet_plans = DjangoFilterConnectionField(MeetPlanType)
