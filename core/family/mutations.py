import strawberry
from strawberry_django.mutations import create

from core.family.inputs import GrandParentInput
from core.family.types import GrandParentType


@strawberry.type
class FamilyMutation:
    create_grandparent: GrandParentType = create(GrandParentInput)
