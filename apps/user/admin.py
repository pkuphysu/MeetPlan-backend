from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import (
    UserCreationForm as BaseUserCreationForm,
    UsernameField,
    UserChangeForm as BaseUserChangeForm,
)
from django.utils.translation import gettext_lazy as _
from guardian.admin import GuardedModelAdminMixin

from apps.user.models import Department, User


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["id", "department"]


class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ("pku_id",)
        field_classes = {"pku_id": UsernameField}


class UserChangeForm(BaseUserChangeForm):
    class Meta:
        model = User
        fields = "__all__"
        field_classes = {"pku_id": UsernameField}


@admin.register(User)
class UserAdmin(GuardedModelAdminMixin, BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("pku_id", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "name",
                    "email",
                    "website",
                    "phone_number",
                    "address",
                    "introduce",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_teacher",
                    "is_admin",
                    "is_staff",
                    "is_superuser",
                    "department",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("pku_id", "password1", "password2"),
            },
        ),
    )
    list_display = ("pku_id", "email", "name", "is_teacher", "is_admin")
    list_filter = (
        "is_teacher",
        "is_admin",
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
        "department",
    )
    search_fields = ("pku_id", "name", "email", "introduce")
    ordering = ("pku_id",)
    add_form = UserCreationForm
    form = UserChangeForm
