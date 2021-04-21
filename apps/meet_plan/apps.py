from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MeetPlanConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.meet_plan"
    verbose_name = _("Meet plan")
