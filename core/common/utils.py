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


def update_object(*, instance, fields: list[str], data: dict):
    update_fields: list[str] = []
    for field in fields:
        if field in data and data[field] is not None:
            setattr(instance, field, data[field])
            update_fields.append(field)

    instance.full_clean()
    instance.save(update_fields=update_fields or None)
    return instance
