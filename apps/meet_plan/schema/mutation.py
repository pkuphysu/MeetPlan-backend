import graphene
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from graphene_django_plus.exceptions import PermissionDenied
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
                raise ValidationError({"teacher": _("You can only create your own meet plan.")})
        else:
            if instance.student_id is None or user.id != instance.student_id:
                raise ValidationError({"student": _("You can only create your own meet plan.")})
            if instance.start_time > timezone.now():
                raise ValidationError({"start_time": _("You can only create the previous plan.")})
            if instance.complete:
                raise ValidationError(
                    {"complete": _("You can only create incomplete plan and ask the teacher to confirm it.")}
                )

    @classmethod
    def after_save(cls, info, instance, cleaned_input=None):
        assign_perm("meet_plan.change_meetplan", instance.teacher, instance)
        assign_perm("meet_plan.delete_meetplan", instance.teacher, instance)


class MeetPlanUpdate(ModelUpdateMutation):
    class Meta:
        model = MeetPlan

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        user = info.context.user
        if user.is_admin:
            pass
        elif user.is_teacher:
            if "teacher" in cleaned_input and cleaned_input["teacher"].id != user.id:
                # 教师只能修改自己的安排
                raise ValidationError({"teacher": _("You can not update the teacher field.")})
        else:
            if (
                ("teacher" in cleaned_input and cleaned_input["teacher"].id != instance.teacher_id)
                or ("start_time" in cleaned_input and cleaned_input["start_time"] != instance.start_time)
                or ("place" in cleaned_input and cleaned_input["place"] != instance.place)
                or ("duration" in cleaned_input and cleaned_input["duration"] != instance.duration)
                or ("t_message" in cleaned_input and cleaned_input["t_message"] != instance.t_message)
            ):
                # 学生不能修改安排信息
                raise ValidationError({"meet_plan": _("You can not modify meet plan details.")})

            if instance.student_id is not None and user.id != instance.student_id:
                # 学生不能修改他人的预约信息
                raise ValidationError({"student": _("You can not modify this.")})

            if instance.student_id is not None and "student" in cleaned_input and cleaned_input["student"] is None:
                # 不允许学生自己取消预约
                raise ValidationError(
                    {"student": _("You can not delete your order, please connect the teacher using email or phone.")}
                )

            if (
                instance.student_id is not None
                and "student" in cleaned_input
                and user.id != cleaned_input["student"].id
            ):
                # 不允许学生将预约信息改成其他人
                raise ValidationError({"student": _("You can not change student field to other student.")})

            if "student" in cleaned_input and user.id != cleaned_input["student"].id:
                # 学生不能帮他人预约信息
                raise ValidationError({"student": _("You can not make order for other student.")})

            if "complete" in cleaned_input and cleaned_input["complete"] and not instance.complete:
                # 学生不能标记预约为已完成
                raise ValidationError({"complete": _("You can not change complete field.")})

        return cleaned_input

    @classmethod
    def before_save(cls, info, instance, cleaned_input=None):
        user = info.context.user
        if user.is_admin:
            pass
        elif user.is_teacher:
            if not user.has_perm("meet_plan.change_meetplan", instance):
                raise ValidationError({"teacher": _("You can only update your own meet plan.")})
        else:
            if instance.start_time < timezone.now():
                # 学生不能修改之前的预约信息
                raise ValidationError({"start_time": _("You can not change previous plan.")})


class MeetPlanDelete(ModelDeleteMutation):
    class Meta:
        model = MeetPlan

    @classmethod
    def get_instance(cls, info, obj_id):
        instance = super().get_instance(info, obj_id)
        user = info.context.user
        if user.is_admin:
            pass
        elif user.is_teacher:
            if not user.has_perm("meet_plan.delete_meetplan", instance):
                raise PermissionDenied()
        else:
            raise PermissionDenied()
        if instance.student and instance.complete:
            raise PermissionDenied(message=_("This plan should not be deleted as it is completed!"))
        return instance


class Mutation(graphene.ObjectType):
    # use create instead of update!!!
    term_date_update = TermDateCreate.Field()

    meet_plan_create = MeetPlanCreate.Field()
    meet_plan_update = MeetPlanUpdate.Field()
    meet_plan_delete = MeetPlanDelete.Field()
