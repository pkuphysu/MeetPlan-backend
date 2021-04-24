import graphene
from graphene_django_plus.types import ModelType

from apps.pku_auth.meta import AbstractMeta, FieldWithDocs
from apps.pku_auth.models import OpenIDClient


class OpenIDClientType(ModelType):
    """
    Offer enough information for frontend to build redirect auth url.\n
    ``https://{authorization_endpoint}?response_type=code&client_id={clientId}
    &scope={scopes}&redirect_uri={redirectUri}[&state={some character}]``
    """

    class Meta(AbstractMeta):
        model = OpenIDClient
        fields = ["authorization_endpoint", "client_id", "redirect_uri", "scopes"]
        allow_unauthenticated = True


class Query(graphene.ObjectType):
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
