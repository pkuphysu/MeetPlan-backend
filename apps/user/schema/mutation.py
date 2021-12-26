import graphene
from django.utils.translation import gettext_lazy as _
from graphene_django_plus.mutations import ModelCreateMutation, ModelUpdateMutation, ModelDeleteMutation
from graphql_jwt.exceptions import PermissionDenied

from apps.user.models import Department, User


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
