#!/usr/bin/env python
"""
Test script to verify that strawberry_generator.py works with individual model files
"""

import os
import sys
from pathlib import Path

import django

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from core.graphql_generator.strawberry_generator import StrawberryCRUDGenerator


def test_individual_files():
    """Test that the generator works with individual model files"""

    try:
        # Initialize the generator with test_app
        generator = StrawberryCRUDGenerator(apps_list=["test_app"])

        # Print loaded models
        for model_name, config in generator.config.items():
            config.get("api_name", "N/A")
            config.get("api_description", "N/A")

            # Show field configuration
            fields_config = config.get("fields", {})
            include_fields = fields_config.get("include", [])
            if include_fields == "__all__":
                pass
            else:
                pass

            # Show relationships
            config.get("relationships", {})

        # Test schema generation
        schema = generator.generate_complete_schema(["test_app"])

        if schema:
            # Print schema info
            query_type = schema.query_type
            mutation_type = schema.mutation_type

            # List some query fields
            query_fields = list(query_type._type_definition.fields.keys())[:5]
            for field in query_fields:
                pass

            # List some mutation fields
            mutation_fields = list(mutation_type._type_definition.fields.keys())[:5]
            for field in mutation_fields:
                pass

        else:
            return False

        return True

    except Exception:
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_individual_files()
    sys.exit(0 if success else 1)
