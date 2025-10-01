from django.db import models

from core.common.models import BaseModel


class GenderChoices(models.TextChoices):
    MALE = "MALE", "Male"
    FEMALE = "FEMALE", "Female"


class GrandParent(BaseModel):
    name = models.CharField(max_length=255)
    gender = models.CharField(max_length=255, choices=GenderChoices.choices, default=GenderChoices.MALE)

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
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
    gender = models.CharField(max_length=255, choices=GenderChoices.choices, default=GenderChoices.MALE)

    class Meta:
        verbose_name = "Child"
        verbose_name_plural = "Children"

    def __str__(self):
        return self.name
