import strawberry
from strawberry_django.mutations import create, delete, update

from core.family.inputs import GrandParentInput, GrandParentPartialInput
from core.family.types import GrandParentType


@strawberry.type
class FamilyMutation:
    create_grandparent: GrandParentType = create(GrandParentInput)
    update_grandparent: GrandParentType = update(GrandParentPartialInput)
    delete_grandparent: GrandParentType = delete(GrandParentPartialInput)
