import strawberry
from strawberry_django.mutations import create
from strawberry_django.permissions import IsAuthenticated

from core.family.inputs import GrandParentInput
from core.family.types import GrandParentType


@strawberry.type
class FamilyMutation:
    create_grandparent: GrandParentType = create(
        GrandParentInput,
        extensions=[IsAuthenticated()],
        # handle_django_errors=True,
    )
