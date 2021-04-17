import graphene
from django.conf import settings
from graphene_django.debug import DjangoDebug

# import apps.meet_plan.schema
import apps.pku_auth.schema
import apps.user.schema


class Query(
    # apps.meet_plan.schema.Query,
    apps.user.schema.Query,
    apps.pku_auth.schema.Query,
    graphene.ObjectType,
):
    if settings.DEBUG:
        debug = graphene.Field(DjangoDebug, name="_debug")


class Mutation(  # apps.meet_plan.schema.Mutation,
    apps.user.schema.Mutation, apps.pku_auth.schema.Mutation, graphene.ObjectType
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
