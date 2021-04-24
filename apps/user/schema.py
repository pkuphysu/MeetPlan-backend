import graphene
from django.utils.translation import gettext_lazy as _
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django_plus.mutations import (
    ModelCreateMutation,
    ModelUpdateMutation,
    ModelDeleteMutation,
)
from graphene_django_plus.types import ModelType
from graphql_jwt.exceptions import PermissionDenied

from apps.pku_auth.meta import AbstractMeta, PKTypeMixin
from apps.user.models import User, Department


class DepartmentType(PKTypeMixin, ModelType):
    class Meta(AbstractMeta):
        model = Department
        fields = ["id", "pk", "department", "user_set"]
        filter_fields = {"id": ["exact", "in"], "department": ["icontains"]}
        allow_unauthenticated = True


class UserType(PKTypeMixin, ModelType):
    class Meta(AbstractMeta):
        model = User
        fields = [
            "id",
            "pk",
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
        filter_fields = {
            "pku_id": ["exact", "contains", "startswith"],
            "name": ["icontains"],
            "department__id": ["exact", "in"],
            "department__department": ["icontains"],
            "is_teacher": ["exact"],
            "is_admin": ["exact"],
            "is_active": ["exact"],
        }

    pku_id = graphene.String(description=_("Only allow user query himself or teacher query student on this field."))

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

    is_active = graphene.Boolean(description=_("Only allow user query himself on this field."))

    @staticmethod
    def resolve_is_active(parent, info):
        if info.context.user.is_admin:
            return parent.is_active
        if info.context.user.id == parent.id:
            return parent.is_active
        raise PermissionDenied

    date_joined = graphene.DateTime(description=_("Only allow user query himself on this field."))

    @staticmethod
    def resolve_date_joined(parent, info):
        if info.context.user.is_admin:
            return parent.date_joined
        if info.context.user.id == parent.id:
            return parent.date_joined
        raise PermissionDenied

    last_login = graphene.DateTime(description=_("Only allow user query himself on this field."))

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


class DepartmentCreate(ModelCreateMutation):
    class Meta:
        model = Department
        permissions = ["user.add_department"]
        only_fields = ["department"]


class DepartmentUpdate(ModelUpdateMutation):
    class Meta:
        model = Department
        permissions = ["user.change_department"]
        only_fields = ["department"]


class DepartmentDelete(ModelDeleteMutation):
    class Meta:
        model = Department
        permissions = ["user.delete_department"]


class MeMutation(ModelUpdateMutation):
    class Meta:
        model = User
        object_permissions = [
            "user.change_user",
        ]
        only_fields = [
            "name",
            "email",
            "website",
            "phone_number",
            "address",
            "department",
            "introduce",
        ]

    @classmethod
    def get_instance(cls, info, obj_id):
        instance = super().get_instance(info, obj_id)
        if instance != info.context.user:
            # 双保险
            raise PermissionDenied(_("This api only allow update yourself."))
        return instance


class UserCreate(ModelCreateMutation):
    class Meta:
        model = User
        permissions = ["user.add_user"]
        only_fields = [
            "pku_id",
            "name",
            "email",
            "website",
            "phone_number",
            "address",
            "introduce",
            "department",
            "is_teacher",
            "is_admin",
            "is_active",
            "groups",
            "user_permissions",
        ]
        exclude_fields = ["password"]


class UserUpdate(ModelUpdateMutation):
    class Meta:
        model = User
        permissions = ["user.change_user"]
        only_fields = [
            "pku_id",
            "name",
            "email",
            "website",
            "phone_number",
            "address",
            "introduce",
            "department",
            "is_teacher",
            "is_admin",
            "is_active",
            "groups",
            "user_permissions",
        ]
        exclude_fields = ["password"]


class UserDelete(ModelDeleteMutation):
    class Meta:
        model = User
        permissions = ["user.delete_user"]


class Mutation(graphene.ObjectType):
    me = MeMutation.Field()

    department_create = DepartmentCreate.Field()
    department_update = DepartmentUpdate.Field()
    department_delete = DepartmentDelete.Field()

    user_create = UserCreate.Field()
    user_update = UserUpdate.Field()
    user_delete = UserDelete.Field()
