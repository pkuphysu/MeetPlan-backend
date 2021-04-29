import graphene
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from graphene_django_plus.mutations import ModelCreateMutation, ModelUpdateMutation, ModelDeleteMutation
from guardian.shortcuts import assign_perm

from apps.meet_plan.models import TermDate, MeetPlan


class TermDateCreate(ModelCreateMutation):
    class Meta:
        model = TermDate
        permissions = ["meet_plan.add_termdate"]
        only_fields = ["start_date"]


class MeetPlanCreate(ModelCreateMutation):
    class Meta:
        model = MeetPlan
        only_fields = [
            "teacher",
            "place",
            "start_time",
            "duration",
            "t_message",
            "student",
            "s_message",
            "complete",
        ]

    @classmethod
    def before_save(cls, info, instance, cleaned_input=None):
        user = info.context.user
        if user.is_admin:
            pass
        elif user.is_teacher:
            if user.id != instance.teacher_id:
                raise ValidationError({"teacher": _("You can only create your own meet plan!")})
        else:
            if instance.student_id is None or user.id != instance.student_id:
                raise ValidationError({"student": _("You can only create your own meet plan!")})
            if instance.start_time > timezone.now():
                raise ValidationError({"start_time": _("You can only create the previous plan!")})
            if instance.complete:
                raise ValidationError(
                    {"complete": _("You can only create incomplete plan and ask the teacher to confirm it!")}
                )

    @classmethod
    def after_save(cls, info, instance, cleaned_input=None):
        assign_perm("meet_plan.change_meetplan", instance.teacher, instance)
        assign_perm("meet_plan.delete_meetplan", instance.teacher, instance)


class MeetPlanUpdate(ModelUpdateMutation):
    class Meta:
        model = MeetPlan


class MeetPlanDelete(ModelDeleteMutation):
    class Meta:
        model = MeetPlan
        obj_permissions = ["meet_plan.delete_meetplan"]


class Mutation(graphene.ObjectType):
    # use create instead of update!!!
    term_date_update = TermDateCreate.Field()

    meet_plan_create = MeetPlanCreate.Field()
    meet_plan_update = MeetPlanUpdate.Field()
    meet_plan_delete = MeetPlanDelete.Field()
