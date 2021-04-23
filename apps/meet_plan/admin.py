from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db import models
from django.db.models import Case, When, Value
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from guardian.admin import GuardedModelAdmin

from apps.meet_plan.models import MeetPlan, TermDate


class AvailableFilter(SimpleListFilter):
    title = _("available")
    parameter_name = "available"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request, queryset):
        now = timezone.now()

        queryset = queryset.annotate(
            available=Case(
                When(start_time__gt=now, student__isnull=True, then=Value(True)),
                output_field=models.BooleanField(),
                default=Value(False),
            ),
        )
        if self.value() == "yes":
            return queryset.filter(available=True)

        if self.value() == "no":
            return queryset.filter(available=False)


@admin.register(MeetPlan)
class MeetPlanAdmin(GuardedModelAdmin):
    list_display = [
        "id",
        "teacher_name",
        "teacher_pku_id",
        "start_time",
        "available",
        "student_name",
        "student_pku_id",
        "complete",
    ]
    list_filter = [AvailableFilter, "complete"]
    search_fields = ["teacher__name", "student__name"]
    list_select_related = ["teacher", "student"]

    @admin.display(description=_("available"), boolean=True)
    def available(self, obj):
        return obj.is_available()

    @admin.display(description=_("Teacher Name"))
    def teacher_name(self, obj):
        return obj.teacher.name

    @admin.display(description=_("Teacher PKU ID"))
    def teacher_pku_id(self, obj):
        link = reverse("admin:user_user_change", args=[obj.teacher_id])
        return mark_safe(f'<a href="{link}">{escape(obj.teacher.pku_id)}</a>')

    @admin.display(empty_value=_("None"), description=_("Student Name"))
    def student_name(self, obj):
        if obj.student:
            return obj.student.name

    @admin.display(empty_value=_("None"), description=_("Student PKU ID"))
    def student_pku_id(self, obj):
        if obj.student:
            link = reverse("admin:user_user_change", args=[obj.student_id])
            return mark_safe(f'<a href="{link}">{escape(obj.student.pku_id)}</a>')


@admin.register(TermDate)
class TermDate(admin.ModelAdmin):
    list_display = ["start_date"]
    ordering = ["-id"]
