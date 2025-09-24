import strawberry
from strawberry_django.optimizer import DjangoOptimizerExtension


@strawberry.type
class Query:
    ping: str = strawberry.field(default="pong")


schema = strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension])


