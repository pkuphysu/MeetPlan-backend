import graphene
from graphene_django_plus.mutations import ModelCreateMutation, ModelUpdateMutation, ModelDeleteMutation

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
