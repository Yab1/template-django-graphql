import strawberry_django

from core.family.models import GrandParent


@strawberry_django.input(GrandParent, fields=["name", "gender"], description="Grand Parent")
class GrandParentInput:
    pass


@strawberry_django.partial(GrandParent, fields=["id", "name", "gender"], description="Grand Parent")
class GrandParentPartialInput:
    pass
