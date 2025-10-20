import strawberry
from gqlauth.core.middlewares import JwtSchema
from strawberry.schema.config import StrawberryConfig
from strawberry.tools import merge_types
from strawberry_django.optimizer import DjangoOptimizerExtension

# Import GraphQL Generator
from core.graphql_generator.strawberry_generator import StrawberryCRUDGenerator

# from core.family.mutations import FamilyMutation  # Removed to avoid conflicts with GraphQL generator
from core.users.mutations import UsersMutation
from core.users.queries import UsersQuery

# Initialize the GraphQL Generator
framework = StrawberryCRUDGenerator()


@strawberry.type
class CommonQuery:
    ping: str = strawberry.field(default="pong")

    @strawberry.field
    def graphql_generator_health_check(self) -> str:
        return "GraphQL Generator is running"


# Generate GraphQL queries and mutations
graphql_schema = framework.generate_complete_schema(["test_app"])

# Merge all queries and mutations
Query = merge_types("Query", (CommonQuery, UsersQuery, graphql_schema.query))
Mutation = merge_types("Mutation", (UsersMutation, graphql_schema.mutation))

# Use JwtSchema to inject request.user and JWT handling
schema = JwtSchema(
    query=Query,
    mutation=Mutation,
    extensions=[DjangoOptimizerExtension],
    config=StrawberryConfig(auto_camel_case=True),
)
