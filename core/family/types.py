import strawberry_django

from .models import Attachments, GrandParent


@strawberry_django.type(GrandParent, fields="__all__", description="Grand Parent")
class GrandParentType:
    profile_picture: "AttachmentsType"


@strawberry_django.type(Attachments, fields="__all__", description="Attachments")
class AttachmentsType:
    pass
