from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import ValidationError

from .models import User
from .services import user_create


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    base_model = User
    list_display: list[str] = [
        "email",
        "full_name",
        "is_staff",
        "is_active",
    ]
    list_filter: list[str] = [
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
    ]
    search_fields: list[str] = ["email", "first_name", "last_name"]
    ordering: list[str] = ["email"]
    fieldsets = (
        (
            "Authentication Info",
            {
                "fields": (
                    "email",
                    "password",
                ),
            },
        ),
        (
            "Personal Info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone_number",
                ),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important Dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "updated_at",
                ),
            },
        ),
    )

    readonly_fields: list[str] = [
        "last_login",
        "date_joined",
        "updated_at",
    ]
    filter_horizontal: list[str] = [
        "groups",
        "user_permissions",
    ]
    show_in_index = True

    def save_model(self, request, obj, form, change):
        if change:
            return super().save_model(request, obj, form, change)

        try:
            user_create(**form.cleaned_data)
        except ValidationError as exc:
            self.message_user(request, str(exc), messages.ERROR)
