from django.db import models

from core.common.models import BaseModel


class GenderChoices(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"


class GrandParent(BaseModel):
    name = models.CharField(max_length=255, help_text="The name of the grandparent")
    gender = models.CharField(
        max_length=255,
        choices=GenderChoices.choices,
        default=GenderChoices.MALE,
        help_text="The gender of the grandparent",
    )
    profile_picture = models.ForeignKey(
        "family.Attachments",
        null=True,
        on_delete=models.CASCADE,
        help_text="The profile picture of the grandparent",
    )

    class Meta:
        verbose_name = "Grand Parent"
        verbose_name_plural = "Grand Parents"

    def __str__(self):
        return self.name


class Parent(BaseModel):
    name = models.CharField(max_length=255)
    grandparent = models.ForeignKey(GrandParent, on_delete=models.CASCADE)
    gender = models.CharField(max_length=255, choices=GenderChoices.choices, default=GenderChoices.MALE)

    class Meta:
        verbose_name = "Parent"
        verbose_name_plural = "Parents"

    def __str__(self):
        return self.name


class Child(BaseModel):
    name = models.CharField(max_length=255, help_text="The name of the child")
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    gender = models.CharField(max_length=255, choices=GenderChoices.choices, default=GenderChoices.MALE)

    class Meta:
        verbose_name = "Child"
        verbose_name_plural = "Children"

    def __str__(self):
        return self.name


class Attachments(BaseModel):
    class ContentTypeChoices(models.TextChoices):
        PDF = "application/pdf", "PDF Document"
        IMAGE_JPEG = "image/jpeg", "JPEG Image"
        IMAGE_PNG = "image/png", "PNG Image"
        TEXT_PLAIN = "text/plain", "Plain Text"
        TEXT_HTML = "text/html", "HTML Document"
        APPLICATION_JSON = "application/json", "JSON Document"
        APPLICATION_XML = "application/xml", "XML Document"

    content_type = models.CharField(
        max_length=100,
        choices=ContentTypeChoices.choices,
        blank=True,
        null=True,
        help_text="Mime type of the content, with charset etc. (e.g., 'text/plain; charset=UTF-8')",
    )
    size = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Number of bytes of content represented (in base64). Used for data attachments.",
    )
    data = models.FileField(upload_to="attachments/", help_text="The data of the attachment")

    class Meta:
        verbose_name = "Attachment"
        verbose_name_plural = "Attachments"

    def __str__(self):
        return self.data
