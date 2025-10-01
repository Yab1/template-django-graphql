import strawberry_django

from .models import GrandParent


@strawberry_django.type(GrandParent, fields="__all__", description="Grand Parent")
class GrandParentType:
    pass
