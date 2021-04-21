from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from apps.pku_auth.signals import user_create
from apps.user.signals import user_create_callback


class UserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.user"
    verbose_name = _("User management")

    def ready(self):
        user_create.connect(receiver=user_create_callback, dispatch_uid="openid_auth_create_user")
