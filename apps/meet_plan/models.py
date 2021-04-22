from django.conf import settings
from django.db import models
from django.db.models import Case, When, Value
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class MeetPlanQuerySet(models.QuerySet):
    def available(self):
        now = timezone.now()
        return self.annotate(
            available=Case(
                When(start_time__gt=now, student__isnull=True, then=Value(True)),
                output_field=models.BooleanField(),
                default=Value(False),
            ),
        )


class MeetPlan(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name="meet_plan")
    place = models.CharField(_("place"), max_length=100)
    start_time = models.DateTimeField(_("start time"))
    duration = models.PositiveSmallIntegerField(
        _("duration"),
        choices=((1, _("half an hour")), (2, _("an hour")), (3, _("an hour and a half")), (4, _("two hours"))),
        default=1,
    )
    t_message = models.TextField(_("teacher message"), blank=True)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name="meet_plan_order", null=True, blank=True
    )
    s_message = models.TextField(_("student message"), blank=True)
    complete = models.BooleanField(_("status"), default=False)

    objects = MeetPlanQuerySet.as_manager()

    class Meta:
        verbose_name = _("meet plan")
        verbose_name_plural = _("meet plans")
        permissions = [("edit_plan", _("Can edit meet plan.")), ("delete_order", _("Can delete meet plan order."))]

    def is_available(self):
        now = timezone.now()
        return self.start_time > now and self.student is None

    def save(self, **kwargs):
        if self.student is None:
            self.s_message = ""
            self.complete = False
        super().save(kwargs)
