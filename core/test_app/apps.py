"""
Test App Django Configuration
Comprehensive test app for GraphQL Generator with all Django field types and relationships
"""

from django.apps import AppConfig


class TestAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.test_app"
    verbose_name = "Test App"
