import strawberry
import strawberry_django

from core.family.inputs import GrandParentInput
from core.family.types import GrandParentType


@strawberry.type
class FamilyMutation:
    create_grandparent: GrandParentType = strawberry_django.mutations.create(GrandParentInput)
