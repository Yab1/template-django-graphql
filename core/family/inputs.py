import strawberry_django

from core.common.utils import inline_input, inline_partial_input
from core.family.models import GrandChild, GrandParent


@strawberry_django.input(GrandParent, fields=["name", "gender"], description="Grand Parent")
class GrandParentInput:
    grand_children: inline_input(
        model=GrandChild,
        fields=["name", "gender"],
        description="Grand Child",
        many=True,
        required=True,
    )


@strawberry_django.partial(GrandParent, fields=["id", "name", "gender"], description="Grand Parent")
class GrandParentPartialInput:
    grand_children: inline_partial_input(
        model=GrandChild,
        fields=["id", "name", "gender"],
        description="Grand Child",
        many=True,
        required=False,
    )
