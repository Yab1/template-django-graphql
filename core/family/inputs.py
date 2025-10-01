import strawberry_django

from core.family.models import GrandParent


@strawberry_django.input(GrandParent, fields="__all__", description="Grand Parent")
class GrandParentInput:
    pass


@strawberry_django.input(GrandParent, fields="__all__", description="Grand Parent")
class GrandParentPartialInput:
    pass
