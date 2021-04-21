from django.contrib import admin
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from guardian.admin import GuardedModelAdmin

from apps.meet_plan.models import MeetPlan


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
    list_filter = ["available", "complete"]
    search_fields = ["teacher__name", "student__name"]
    list_select_related = ["teacher", "student"]

    @admin.display(description=_("Teacher Name"))
    def teacher_name(self, obj):
        link = reverse("admin:user_user_change", args=[obj.teacher_id])
        return mark_safe(f'<a href="{link}">{escape(obj.teacher.name)}</a>')

    @admin.display(description=_("Teacher PKU ID"))
    def teacher_pku_id(self, obj):
        link = reverse("admin:user_user_change", args=[obj.teacher_id])
        return mark_safe(f'<a href="{link}">{escape(obj.teacher.pku_id)}</a>')

    @admin.display(empty_value=_("None"), description=_("Student Name"))
    def student_name(self, obj):
        if obj.student:
            link = reverse("admin:user_user_change", args=[obj.student_id])
            return mark_safe(f'<a href="{link}">{escape(obj.student.name)}</a>')

    @admin.display(empty_value=_("None"), description=_("Student PKU ID"))
    def student_pku_id(self, obj):
        if obj.student:
            link = reverse("admin:user_user_change", args=[obj.student_id])
            return mark_safe(f'<a href="{link}">{escape(obj.student.pku_id)}</a>')
