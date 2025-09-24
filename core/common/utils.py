from django.http import Http404
from django.shortcuts import get_list_or_404, get_object_or_404


def get_list(model_or_queryset, **kwargs):
    try:
        return get_list_or_404(model_or_queryset)
    except Http404 as exc:
        raise exc


def get_object(model_or_queryset, **kwargs):
    try:
        return get_object_or_404(model_or_queryset, **kwargs)
    except Http404:
        return None


def update_object(obj, **kwargs):
    for key, value in kwargs.items():
        setattr(obj, key, value)

    obj.save()

    return obj


def create_serializer_class(name, fields):
    # No-op placeholder to keep API compatibility if needed in future
    raise NotImplementedError("Serializers are not available without DRF.")


def inline_serializer(*, fields, data=None, **kwargs):
    raise NotImplementedError("inline_serializer is not available without DRF.")
