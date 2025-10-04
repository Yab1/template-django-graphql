import strawberry_django
from strawberry.file_uploads import Upload

from core.family.models import Attachments, GrandParent


@strawberry_django.input(GrandParent, fields=["name", "gender"], description="Grand Parent")
class GrandParentInput:
    profile_picture: "AttachmentsInput"


@strawberry_django.partial(GrandParent, fields=["id", "name", "gender"], description="Grand Parent")
class GrandParentPartialInput:
    pass


@strawberry_django.input(Attachments, fields=["content_type", "size"], description="Attachments")
class AttachmentsInput:
    data: Upload
