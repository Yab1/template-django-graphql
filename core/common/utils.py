from typing import Any, Dict, Mapping, Optional

from django.http import Http404
from django.shortcuts import get_list_or_404, get_object_or_404

try:
    # Keep DRF utilities working for existing inline_serializer usage
    from rest_framework import serializers  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    serializers = None  # type: ignore

import strawberry_django


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


def create_object(*, model, data):
    # Handle both dict and object inputs
    if hasattr(data, "__dict__"):
        # Convert object to dict and filter out None values
        data_dict = {k: v for k, v in data.__dict__.items() if v is not None}
    else:
        # If it's already a dict, filter out None values
        data_dict = {k: v for k, v in data.items() if v is not None}

    return model.objects.create(**data_dict)


def update_object(*, instance, fields: list[str], data: dict):
    update_fields: list[str] = []
    for field in fields:
        if field in data and data[field] is not None:
            setattr(instance, field, data[field])
            update_fields.append(field)

    instance.full_clean()
    instance.save(update_fields=update_fields or None)
    return instance


def create_serializer_class(name, fields):
    if serializers is None:
        raise RuntimeError("djangorestframework is required for create_serializer_class/inline_serializer")
    return type(name, (serializers.Serializer,), fields)


def inline_serializer(*, fields, data=None, **kwargs):
    # Get custom name if provided, otherwise create a unique name based on fields
    custom_name = kwargs.pop("name", None)
    name = custom_name if custom_name else f"InlineSerializer_{hash(frozenset(fields.items()))}"

    # Cache the serializer class to avoid recreation
    if not hasattr(inline_serializer, "_classes"):
        inline_serializer._classes = {}

    # If a custom name is provided, always create a new class to avoid conflicts
    if custom_name or name not in inline_serializer._classes:
        serializer_class = create_serializer_class(name, fields)
        # Only cache if no custom name was provided
        if not custom_name:
            inline_serializer._classes[name] = serializer_class
    else:
        serializer_class = inline_serializer._classes[name]

    if data is not None:
        return serializer_class(data=data, **kwargs)

    return serializer_class(**kwargs)


# ---------------------------------------------------------------------------
# Strawberry Django: inline input builders
# ---------------------------------------------------------------------------

_INLINE_INPUT_CACHE: Dict[tuple, type] = {}
_INLINE_TYPE_CACHE: Dict[tuple, type] = {}


def _build_inline_input_class(
    *,
    model: Any,
    fields: list[str],
    description: Optional[str],
    name: Optional[str],
    extra_annotations: Optional[Mapping[str, Any]],
    decorator: Any,
):
    """Create (and cache) a Strawberry Django input/partial class.

    This dynamically constructs a class, then applies strawberry_django's
    decorator to turn it into a valid Strawberry input type.
    """

    annotations: Dict[str, Any] = dict(extra_annotations or {})

    cache_key = (
        decorator.__name__ if hasattr(decorator, "__name__") else str(decorator),
        model,
        tuple(fields),
        description,
        tuple(sorted(annotations.items(), key=lambda item: item[0])),
        name,
    )

    # Only cache when name is not explicitly provided (explicit names may be reused intentionally)
    if name is None and cache_key in _INLINE_INPUT_CACHE:
        return _INLINE_INPUT_CACHE[cache_key]

    class_name = name or (
        f"Inline{getattr(model, "__name__", "Model")}Input"
        if decorator is strawberry_django.input
        else f"Inline{getattr(model, "__name__", "Model")}PartialInput"
    )

    namespace: Dict[str, Any] = {"__annotations__": annotations}

    # Build a bare Python class, then decorate it via strawberry_django
    cls = type(class_name, (object,), namespace)
    wrapped = decorator(model, fields=fields, description=description)(cls)

    if name is None:
        _INLINE_INPUT_CACHE[cache_key] = wrapped

    return wrapped


def _apply_many_required(base_type: Any, *, many: bool, required: bool) -> Any:
    """Return an annotation adjusted for cardinality and optionality.

    - If many is True, annotate as a list of the base type.
    - If required is False, annotate as Optional[...] (using | None syntax).

    This keeps field annotations concise and consistent across inputs and types.
    """

    annotated: Any = base_type
    if many:
        annotated = list[annotated]
    if not required:
        annotated = annotated | None
    return annotated


def inline_input(
    *,
    model: Any,
    fields: list[str],
    description: Optional[str] = None,
    name: Optional[str] = None,
    extra_annotations: Optional[Mapping[str, Any]] = None,
    many: bool = False,
    required: bool = True,
):
    """Construct a Strawberry Django input type inline for field annotations.

    This returns a dynamically created Strawberry input class that you can use
    directly inside annotations without declaring a separate class.

    Args:
        model: Django model class that the input maps to.
        fields: List of field names to expose on the input.
        description: Optional description for the generated input type.
        name: Optional explicit class name; when omitted a cached name is used.
        extra_annotations: Optional extra type annotations to add as fields.
        many: If True, annotate as a list of this input. Defaults to False.
        required: If False, annotate as Optional[...] (| None). Defaults to True.

    Examples:
        Single required child:
            child: inline_input(model=Child, fields=["name", "gender"])  # required single

        Optional single child:
            child: inline_input(model=Child, fields=["name"], required=False)

        Required list of children:
            children: inline_input(model=Child, fields=["name"], many=True)

        Optional list of children:
            children: inline_input(model=Child, fields=["name"], many=True, required=False)
    """

    base = _build_inline_input_class(
        model=model,
        fields=fields,
        description=description,
        name=name,
        extra_annotations=extra_annotations,
        decorator=strawberry_django.input,
    )
    return _apply_many_required(base, many=many, required=required)


def inline_partial_input(
    *,
    model: Any,
    fields: list[str],
    description: Optional[str] = None,
    name: Optional[str] = None,
    extra_annotations: Optional[Mapping[str, Any]] = None,
    many: bool = False,
    required: bool = True,
):
    """Construct a Strawberry Django partial input type inline for updates.

    Fields behave like Django's partial updates: only provided fields are
    validated/updated. Use ``many`` and ``required`` to control cardinality and
    optionality of the annotation similarly to ``inline_input``.

    Args:
        model: Django model class.
        fields: Field names to expose; typically includes "id" for PATCH/PUT.
        description: Optional description.
        name: Optional explicit class name.
        extra_annotations: Optional extra type annotations.
        many: If True, return a list annotation of this partial input.
        required: If False, mark the annotation as Optional.
    """

    base = _build_inline_input_class(
        model=model,
        fields=fields,
        description=description,
        name=name,
        extra_annotations=extra_annotations,
        decorator=strawberry_django.partial,
    )
    return _apply_many_required(base, many=many, required=required)


# ---------------------------------------------------------------------------
# Strawberry Django: inline type builder (output types)
# ---------------------------------------------------------------------------


def _build_inline_type_class(
    *,
    model: Any,
    fields: Any,
    description: Optional[str],
    name: Optional[str],
    extra_annotations: Optional[Mapping[str, Any]],
):
    annotations: Dict[str, Any] = dict(extra_annotations or {})

    cache_key = (
        "type",
        model,
        tuple(fields) if isinstance(fields, (list, tuple)) else fields,
        description,
        tuple(sorted(annotations.items(), key=lambda item: item[0])),
        name,
    )

    if name is None and cache_key in _INLINE_TYPE_CACHE:
        return _INLINE_TYPE_CACHE[cache_key]

    class_name = name or f"Inline{getattr(model, "__name__", "Model")}Type"

    namespace: Dict[str, Any] = {"__annotations__": annotations}
    cls = type(class_name, (object,), namespace)
    wrapped = strawberry_django.type(model, fields=fields, description=description)(cls)

    if name is None:
        _INLINE_TYPE_CACHE[cache_key] = wrapped

    return wrapped


def inline_type(
    *,
    model: Any,
    fields: Any = "__all__",
    description: Optional[str] = None,
    name: Optional[str] = None,
    extra_annotations: Optional[Mapping[str, Any]] = None,
    many: bool = False,
    required: bool = True,
):
    """Construct a Strawberry Django output type inline for field annotations.

    Useful for referencing nested types without importing or declaring full
    classes. Mirrors the API of ``inline_input`` for consistency.

    Args:
        model: Django model class.
        fields: Field selection for the type ("__all__" or list of names).
        description: Optional description text.
        name: Optional explicit class name (disables cache reuse when set).
        extra_annotations: Optional extra type annotations to add as fields.
        many: If True, return a list annotation of this type.
        required: If False, mark the annotation as Optional.

    Examples:
        Required list of nested children:
            grand_children: inline_type(model=GrandChild, fields="__all__", many=True)

        Optional single nested relation:
            parent: inline_type(model=GrandChild, fields="__all__", required=False)
    """
    base = _build_inline_type_class(
        model=model,
        fields=fields,
        description=description,
        name=name,
        extra_annotations=extra_annotations,
    )
    return _apply_many_required(base, many=many, required=required)
