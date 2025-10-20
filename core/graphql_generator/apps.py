"""
GraphQL Generator Django App Configuration
"""

from django.apps import AppConfig


class GraphQLGeneratorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.graphql_generator"
    verbose_name = "GraphQL Generator"
