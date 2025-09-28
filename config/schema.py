import strawberry
from gqlauth.core.middlewares import JwtSchema
from strawberry.schema.config import StrawberryConfig
from strawberry.tools import merge_types
from strawberry_django.optimizer import DjangoOptimizerExtension

from core.users.mutations import UsersMutation
from core.users.queries import UsersQuery


@strawberry.type
class CommonQuery:
    ping: str = strawberry.field(default="pong")


Query = merge_types("Query", (CommonQuery, UsersQuery))
Mutation = merge_types("Mutation", (UsersMutation,))


# Use JwtSchema to inject request.user and JWT handling
schema = JwtSchema(
    query=Query,
    mutation=Mutation,
    extensions=[DjangoOptimizerExtension],
    config=StrawberryConfig(auto_camel_case=True),
)
