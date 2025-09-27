from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["id", "document_type", "document_name", "document_path", "uploaded_by"]
    list_filter = ["document_type", "uploaded_by"]
    search_fields = ["document_name", "uploaded_by__email"]
    readonly_fields = ["document_path", "uploaded_by"]
    ordering = ["-created_at"]
    show_in_index = True
    list_per_page = 10
