from calendar import timegm
from functools import wraps

import graphene
import graphql_jwt
from django.contrib.auth import authenticate, user_logged_in
from django.utils.translation import gettext as _
from graphene.utils.thenables import maybe_thenable
from graphene_django_plus.types import ModelType
from graphql_jwt import exceptions, signals
from graphql_jwt.decorators import setup_jwt_cookie, csrf_rotation, refresh_expiration, on_token_auth_resolve
from graphql_jwt.mixins import ObtainJSONWebTokenMixin
from graphql_jwt.refresh_token.decorators import ensure_refresh_token
from graphql_jwt.refresh_token.shortcuts import get_refresh_token
from graphql_jwt.refresh_token.utils import get_refresh_token_model

import apps.user.schema
from apps.pku_auth.meta import AbstractMeta
from apps.pku_auth.models import OpenIDClient


def token_auth(f):
    @wraps(f)
    @setup_jwt_cookie
    @csrf_rotation
    @refresh_expiration
    def wrapper(cls, root, info, code, **kwargs):
        context = info.context
        context._jwt_token_auth = True

        user = authenticate(
            request=context,
            code=code,
        )
        if user is None:
            raise exceptions.JSONWebTokenError(
                _('Please enter valid credentials'),
            )

        if hasattr(context, 'user'):
            context.user = user

        result = f(cls, root, info, **kwargs)
        signals.token_issued.send(sender=cls, request=context, user=user)
        user_logged_in.send(sender=cls, user=user)
        return maybe_thenable((context, user, result), on_token_auth_resolve)

    return wrapper


class ObtainJSONWebToken(ObtainJSONWebTokenMixin, graphene.Mutation):
    """
    Use this for login user in.\n
    Then add a option in http header:\n
    \tAuthorization: JWT <token> \n
    payload include user.ID & token expire timestamp
    """
    user = graphene.Field(apps.user.schema.UserType)

    @classmethod
    def resolve(cls, root, info, **kwargs):
        return cls(user=info.context.user)

    @classmethod
    def Field(cls, *args, **kwargs):
        cls._meta.arguments.update({
            'code': graphene.String(required=True),
        })
        return super().Field(*args, **kwargs)

    @classmethod
    @token_auth
    def mutate(cls, root, info, **kwargs):
        return cls.resolve(root, info, **kwargs)


class OpenIDClientType(ModelType):
    """
    Offer enough information for frontend to build redirect auth url.\n
    \thttps://{authorization_endpoint}?response_type=code&client_id={clientId}&scope={scopes}&redirect_uri={redirectUri}[&state={some character}]
    """

    class Meta(AbstractMeta):
        model = OpenIDClient
        fields = [
            'authorization_endpoint',
            'client_id',
            'redirect_uri',
            'scopes'
        ]
        allow_unauthenticated = True


class Query(graphene.ObjectType):
    from .meta import FieldWithDocs
    openid_client = FieldWithDocs(OpenIDClientType)

    @staticmethod
    def resolve_openid_client(root, info):
        """
        TODO: when https://github.com/tfoxy/graphene-django-optimizer release support graphene v3
        try this
        import graphene_django_optimizer as gql_optimizer
        return gql_optimizer.query(OpenIDClient.objects.last(), info)
        """
        return OpenIDClient.objects.last()


class Verify(graphql_jwt.Verify):
    """
    Use this to get payload from token.\n
    """


class Refresh(graphql_jwt.Refresh):
    """
    Use this to get new token with refreshToken.
    """


class Revoke(graphql_jwt.Revoke):
    """
    Use this to revoke fresh token.
    """


class RevokeAll(graphene.Mutation):
    """
    Use this to revoke all fresh tokens issued to the user.
    """

    class Arguments:
        refresh_token = graphene.String()

    revoked = graphene.Int(required=True)

    @classmethod
    @ensure_refresh_token
    def revoke(cls, root, info, refresh_token, **kwargs):
        context = info.context
        refresh_token_obj = get_refresh_token(refresh_token, context)
        refresh_token_objs = get_refresh_token_model().objects.filter(user=refresh_token_obj.user)
        for refresh_token_obj in refresh_token_objs:
            refresh_token_obj.revoke(context)
        return cls(revoked=timegm(refresh_token_obj.revoked.timetuple()))

    @classmethod
    def mutate(cls, *args, **kwargs):
        return cls.revoke(*args, **kwargs)


class Mutation(graphene.ObjectType):
    code_auth = ObtainJSONWebToken.Field()
    verify_token = Verify.Field()
    refresh_token = Refresh.Field()
    revoke_token = Revoke.Field()
    revoke_token_all = RevokeAll.Field()
