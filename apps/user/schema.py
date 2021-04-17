import graphene
from django.utils.translation import gettext_lazy as _
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django_plus.types import ModelType
from graphql_jwt.exceptions import PermissionDenied

from apps.pku_auth.meta import AbstractMeta
from apps.user.models import User, Department


class DepartmentType(ModelType):
    class Meta(AbstractMeta):
        description = _("123")
        model = Department
        fields = ["id", "department", "user_set"]
        filter_fields = {"department": ["icontains"]}
        allow_unauthenticated = True


class UserType(ModelType):
    class Meta(AbstractMeta):
        model = User
        fields = [
            "id",
            # 'pku_id',
            "name",
            "email",
            "website",
            "phone_number",
            "address",
            "is_teacher",
            "department",
            "introduce",
            "is_admin",
            # 'is_active',
            # 'date_joined',
            # 'last_login',
        ]
        filter_fields = [
            "id",
            "pku_id",
            "name",
            "department__department",
            "is_teacher",
            "is_admin",
            "is_active",
        ]
        allow_unauthenticated = True
        convert_choices_to_enum = []

    pku_id = graphene.String(
        description=_(
            "Only allow user query himself or teacher query student on this field."
        )
    )

    @staticmethod
    def resolve_pku_id(parent, info):
        if info.context.user.is_admin:
            return parent.pku_id
        if info.context.user.is_teacher:
            if not parent.is_teacher:
                return parent.pku_id
        if info.context.user.id == parent.id:
            return parent.pku_id
        raise PermissionDenied

    is_active = graphene.Boolean(
        description=_("Only allow user query himself on this field.")
    )

    @staticmethod
    def resolve_is_active(parent, info):
        if info.context.user.is_admin:
            return parent.is_active
        if info.context.user.id == parent.id:
            return parent.is_active
        raise PermissionDenied

    date_joined = graphene.DateTime(
        description=_("Only allow user query himself on this field.")
    )

    @staticmethod
    def resolve_date_joined(parent, info):
        if info.context.user.is_admin:
            return parent.date_joined
        if info.context.user.id == parent.id:
            return parent.date_joined
        raise PermissionDenied

    last_login = graphene.DateTime(
        description=_("Only allow user query himself on this field.")
    )

    @staticmethod
    def resolve_last_login(parent, info):
        if info.context.user.is_admin:
            return parent.last_login
        if info.context.user.id == parent.id:
            return parent.last_login
        raise PermissionDenied

    @classmethod
    def get_queryset(cls, qs, info):
        if info.context.user.is_authenticated:
            return super().get_queryset(qs, info)
        return User.objects.none()


class Query(graphene.ObjectType):
    me = graphene.Field(UserType)

    @staticmethod
    def resolve_me(parent, info):
        if info.context.user.is_authenticated:
            return info.context.user
        return None

    department = relay.Node.Field(DepartmentType)
    departments = DjangoFilterConnectionField(DepartmentType)

    user = relay.Node.Field(UserType)
    users = DjangoFilterConnectionField(UserType)


class Mutation(graphene.ObjectType):
    pass
