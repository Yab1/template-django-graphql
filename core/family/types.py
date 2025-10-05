import strawberry_django

from core.common.utils import inline_type
from core.family.models import Child, GrandChild, GrandParent


@strawberry_django.type(GrandParent, fields="__all__", description="Grand Parent")
class GrandParentType:
    grand_children: inline_type(
        model=GrandChild,
        fields="__all__",
        description="Grand Child",
        many=True,
        required=True,
    )


@strawberry_django.type(GrandChild, fields="__all__", description="Grand Child")
class GrandChildType:
    pass


@strawberry_django.type(Child, fields="__all__", description="Child")
class ChildType:
    parent: inline_type(
        model=GrandChild,
        fields="__all__",
        description="Grand Child",
        many=False,
        required=True,
    )
