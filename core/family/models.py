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

    class Meta:
        verbose_name = "Grand Parent"
        verbose_name_plural = "Grand Parents"

    def __str__(self):
        return self.name


class GrandChild(BaseModel):
    name = models.CharField(max_length=255)
    grand_parent = models.ForeignKey(GrandParent, on_delete=models.CASCADE, related_name="grand_children")
    gender = models.CharField(max_length=255, choices=GenderChoices.choices, default=GenderChoices.MALE)

    class Meta:
        verbose_name = "Grand Child"
        verbose_name_plural = "Grand Children"

    def __str__(self):
        return self.name


class Child(BaseModel):
    name = models.CharField(max_length=255, help_text="The name of the child")
    parent = models.ForeignKey(GrandChild, on_delete=models.CASCADE, related_name="children")
    gender = models.CharField(max_length=255, choices=GenderChoices.choices, default=GenderChoices.MALE)

    class Meta:
        verbose_name = "Child"
        verbose_name_plural = "Children"

    def __str__(self):
        return self.name
