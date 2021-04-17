from django.apps import AppConfig
from apps.pku_auth.signals import user_create
from apps.user.signals import user_create_callback


class UserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.user"

    def ready(self):
        user_create.connect(
            receiver=user_create_callback, dispatch_uid="openid_auth_create_user"
        )
