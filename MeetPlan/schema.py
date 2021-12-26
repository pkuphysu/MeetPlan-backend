import graphene
from django.conf import settings
from graphene_django.debug import DjangoDebug

from apps.meet_plan.schema import Query as MeetPlanQuery, Mutation as MeetPlanMutation
from apps.pku_auth.schema import Query as AuthQuery, Mutation as AuthMutation
from apps.user.schema import Query as UserQuery, Mutation as UserMutation


class Query(MeetPlanQuery, UserQuery, AuthQuery, graphene.ObjectType):
    if settings.DEBUG:
        debug = graphene.Field(DjangoDebug, name="_debug")


class Mutation(MeetPlanMutation, UserMutation, AuthMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
