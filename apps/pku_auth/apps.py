from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OpenidClientConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.pku_auth"
    verbose_name = _("Openid Client")
