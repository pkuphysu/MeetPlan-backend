from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class MeetPlan(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name="meet_plan")
    place = models.CharField(_("place"), max_length=100)
    start_time = models.DateTimeField(_("start time"))
    duration = models.PositiveSmallIntegerField(
        _("duration"),
        choices=((1, _("half an hour")), (2, _("an hour")), (3, _("an hour and a half")), (4, _("two hours"))),
    )
    t_message = models.TextField(_("teacher message"), blank=True)
    available = models.BooleanField(_("available"), default=True, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, related_name="meet_plan_order", null=True, blank=True
    )
    s_message = models.TextField(_("student message"), blank=True)
    complete = models.BooleanField(_("status"), default=False)

    class Meta:
        verbose_name = _("meet plan")
        verbose_name_plural = _("meet plans")
        permissions = [("edit_plan", _("Can edit meet plan.")), ("delete_order", _("Can delete meet plan order."))]

    def save(self, **kwargs):
        if self.student:
            self.available = False
        else:
            self.available = True
        super(MeetPlan, self).save(**kwargs)
