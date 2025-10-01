from django.db import models


class GrandParent(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Grand Parent"
        verbose_name_plural = "Grand Parents"

    def __str__(self):
        return self.name


class Parent(models.Model):
    name = models.CharField(max_length=255)
    grandparent = models.ForeignKey(GrandParent, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Parent"
        verbose_name_plural = "Parents"

    def __str__(self):
        return self.name


class Child(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Child"
        verbose_name_plural = "Children"

    def __str__(self):
        return self.name
