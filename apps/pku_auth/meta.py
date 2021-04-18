import graphene
from graphene import relay
from graphene_django_plus.fields import CountableConnection


class AbstractMeta:
    """
    An abstract meta class for graphene_django_plus.types.ModelType.

    **Extra options**

    ``AbstractMeta.convert_choices_to_enum``

        *Default*: ``[]``

        Disable the automatic conversion on any Django fields that have
        choices defined into a GraphQL enum type.

    ``AbstractMeta.interfaces``

        *Default*: ``(graphene.relay.Node)``

    ``AbstractMeta.connection_class``

        *Default*: ``graphene_django_plus.fields.CountableConnection``

        Connection that provides a total_count attribute.

    ``AbstractMeta.allow_unauthenticated``

        *Default*: ``False``

        If unauthenticated users should be allowed to retrieve any object
        of this type. This is not dependant on `GuardedModel` and neither
        `guardian` and is defined as `False` by default.

    ``AbstractMeta.permissions``

        *Default*: ``[]``

        A list of Django model permissions to check. Different from
        object_permissions, this uses the basic Django's permission system
        and thus is not dependant on `GuardedModel` and neither `guardian`.
        This is an empty list by default.

    ``AbstractMeta.object_permissions``

        *Default*: ``[]``

        When adding this to a query, only objects with a `can_read`
        permission to the request's user will be allowed to return to him
        Note that `can_read` was defined in the model.
        If the model doesn't inherid from `GuardedModel`, `guardian` is not
        installed ot this list is empty, any object will be allowed.
        This is empty by default.

    """

    class Meta:
        abstract = True

    convert_choices_to_enum = []
    interfaces = (relay.Node,)
    connection_class = CountableConnection
    allow_unauthenticated = False
    object_permissions = []
    permissions = []


class FieldWithDocs(graphene.Field):
    def __init__(self, type_, description=None, **extra_args):
        super().__init__(type_, description=description or type_._meta.description, **extra_args)


class PKTypeMixin:
    pk = graphene.Int(description="used for foreign key filtering")
