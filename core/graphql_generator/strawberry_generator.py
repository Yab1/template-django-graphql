"""
Strawberry Django CRUD Generator - Dynamic GraphQL Generation
Based on the graphi_crud pattern but for Strawberry Django
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import strawberry
import yaml
from asgiref.sync import sync_to_async


# Import Django components only when needed
def get_django_components():
    from django.apps import apps
    from django.db import models

    return apps, models


logger = logging.getLogger(__name__)


class StrawberryCRUDGenerator:
    """Dynamic GraphQL CRUD Generator for Strawberry Django"""

    def __init__(self, apps_list: List[str] = None):
        self.apps_list = apps_list or []
        self.config = self._load_yaml_config(self.apps_list) if self.apps_list else {}
        self.generated_types = {}
        self.generated_enums = {}

    def _load_yaml_config(self, apps_list: List[str]) -> Dict[str, Any]:
        """Load YAML configuration from each app's gql_config folder"""
        all_configs = {}

        for app_name in apps_list:
            try:
                app_config_dir = Path(__file__).parent.parent.parent / "core" / app_name / "gql_config"

                if not app_config_dir.exists():
                    logger.warning(f"No gql_config folder found for app: {app_name}")
                    continue

                # Load defaults first
                defaults = self._load_defaults(app_config_dir)

                # Try to load single models.yml file first
                single_config_path = app_config_dir / "models.yml"
                if single_config_path.exists():
                    with open(single_config_path, "r") as file:
                        models_config = yaml.safe_load(file)
                        # Handle the case where models are nested under 'models' key
                        if "models" in models_config:
                            for model_name, model_config in models_config["models"].items():
                                merged_config = self._merge_with_defaults(defaults, model_config)
                                all_configs[model_name] = merged_config
                        else:
                            # Handle the case where models are at the top level
                            for model_name, model_config in models_config.items():
                                if model_name != "defaults":
                                    merged_config = self._merge_with_defaults(defaults, model_config)
                                    all_configs[model_name] = merged_config
                        logger.info(f"Loaded single models.yml for app: {app_name}")
                        continue

                # Load individual model files
                model_files = list(app_config_dir.glob("*.yml"))
                model_files = [f for f in model_files if f.name != "defaults.yml"]

                for model_file in model_files:
                    with open(model_file, "r") as file:
                        model_config = yaml.safe_load(file)
                        model_name = model_config.get("model")
                        if model_name:
                            merged_config = self._merge_with_defaults(defaults, model_config)
                            all_configs[model_name] = merged_config
                            logger.info(f"Loaded {model_file.name} for app: {app_name}")

                if not all_configs:
                    logger.warning(f"No model configurations found for app: {app_name}")

            except Exception as e:
                logger.error(f"Error loading YAML config for app {app_name}: {e}")
                continue

        return all_configs

    def _load_defaults(self, app_config_dir: Path) -> Dict[str, Any]:
        """Load default configuration for an app"""
        defaults_path = app_config_dir / "defaults.yml"
        if defaults_path.exists():
            with open(defaults_path, "r") as file:
                defaults_config = yaml.safe_load(file)
                return defaults_config.get("defaults", {})
        return {}

    def _merge_with_defaults(self, defaults: dict, model_config: dict) -> dict:
        """Merge model configuration with defaults"""
        merged = defaults.copy()

        def deep_merge(d1, d2):
            for key, value in d2.items():
                if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
                    deep_merge(d1[key], value)
                else:
                    d1[key] = value

        deep_merge(merged, model_config)
        return merged

    def find_all_models(self, apps_list: List[str]) -> List:
        """Find all models in specified apps"""
        apps, _models = get_django_components()
        found_models = []

        # Load config if not already loaded
        if not self.config:
            self.config = self._load_yaml_config(apps_list)

        for app_name in apps_list:
            try:
                app_config = apps.get_app_config(app_name)
                models_list = app_config.get_models()
                for model in models_list:
                    # Check if model has YAML configuration
                    if model.__name__ in self.config:
                        found_models.append(model)
                        logger.info(f"Found model: {model.__name__} in app: {app_name}")
            except Exception as e:
                logger.error(f"Error processing app {app_name}: {e}")
                continue

        return found_models

    def generate_enum_from_choices(self, field) -> Optional[Type[Enum]]:
        """Generate Strawberry enum from Django field choices"""
        if not hasattr(field, "choices") or not field.choices:
            return None

        # Create enum class dynamically
        enum_name = f"{field.model.__name__}{field.name.title()}Enum"

        if enum_name in self.generated_enums:
            return self.generated_enums[enum_name]

        # Create enum values
        enum_values = {}
        for choice_value, choice_label in field.choices:
            # Convert to valid Python identifier
            key = choice_value.upper().replace(" ", "_").replace("-", "_")
            enum_values[key] = choice_value

        # Create the enum class using Enum constructor
        enum_class = Enum(enum_name, enum_values)

        # Make it a Strawberry enum
        strawberry_enum = strawberry.enum(enum_class)

        self.generated_enums[enum_name] = strawberry_enum
        return strawberry_enum

    def get_strawberry_field_type(self, field) -> Any:
        """Convert Django field to Strawberry field type"""
        field_type = field.get_internal_type()

        # Handle choice fields
        if hasattr(field, "choices") and field.choices:
            enum_type = self.generate_enum_from_choices(field)
            if enum_type:
                return enum_type

        # Handle different field types
        if field_type in ["CharField", "TextField", "EmailField", "URLField"]:
            return str
        if field_type in ["IntegerField", "BigIntegerField", "SmallIntegerField"]:
            return int
        if field_type in ["FloatField", "DecimalField"]:
            return float
        if field_type in ["BooleanField"]:
            return bool
        if field_type in ["DateTimeField"]:
            return strawberry.auto
        if field_type in ["DateField"]:
            return strawberry.auto
        if field_type in ["UUIDField"]:
            return strawberry.ID
        if field_type in ["ForeignKey", "OneToOneField"]:
            # Return the related model type (will be generated later)
            return strawberry.ID  # For now, return ID
        if field_type in ["ManyToManyField"]:
            return List[strawberry.ID]  # For now, return list of IDs

        # Default to string
        return str

    def generate_input_type(self, model) -> Type:
        """Generate Strawberry input type for a model"""
        model_name = model.__name__
        input_name = f"{model_name}Input"

        if input_name in self.generated_types:
            return self.generated_types[input_name]

        # Get model configuration
        config = self.config.get(model_name, {})
        fields_config = config.get("fields", {})
        include_fields = fields_config.get("include", [])
        exclude_fields = fields_config.get("exclude", [])

        # Build field definitions
        attrs = {"__annotations__": {}}

        for field in model._meta.fields:
            if field.name in exclude_fields:
                continue

            if include_fields and field.name not in include_fields:
                continue

            # Skip auto fields and ID fields for input (they will be generated automatically)
            if field.get_internal_type() in ["AutoField", "BigAutoField", "UUIDField"]:
                continue

            field_type = self.get_strawberry_field_type(field)
            attrs["__annotations__"][field.name] = field_type

        # Create the input type
        input_type = type(input_name, (), attrs)
        strawberry_input = strawberry.input(input_type)

        self.generated_types[input_name] = strawberry_input
        return strawberry_input

    def generate_update_input_type(self, model) -> Type:
        """Generate Strawberry update input type for a model"""
        model_name = model.__name__
        input_name = f"{model_name}UpdateInput"

        if input_name in self.generated_types:
            return self.generated_types[input_name]

        # Get model configuration
        config = self.config.get(model_name, {})
        fields_config = config.get("fields", {})
        include_fields = fields_config.get("include", [])
        exclude_fields = fields_config.get("exclude", [])

        # Build field definitions
        attrs = {"__annotations__": {"id": strawberry.ID}}  # Always include ID for updates

        for field in model._meta.fields:
            if field.name in exclude_fields:
                continue

            if include_fields and field.name not in include_fields:
                continue

            # Skip auto fields and ID fields for input (they will be generated automatically)
            if field.get_internal_type() in ["AutoField", "BigAutoField", "UUIDField"]:
                continue

            field_type = self.get_strawberry_field_type(field)
            attrs["__annotations__"][field.name] = field_type

        # Create the input type
        input_type = type(input_name, (), attrs)
        strawberry_input = strawberry.input(input_type)

        self.generated_types[input_name] = strawberry_input
        return strawberry_input

    def generate_output_type(self, model) -> Type:
        """Generate Strawberry output type for a model"""
        model_name = model.__name__
        output_name = f"{model_name}Type"

        if output_name in self.generated_types:
            return self.generated_types[output_name]

        # Get model configuration
        config = self.config.get(model_name, {})
        fields_config = config.get("fields", {})
        include_fields = fields_config.get("include", [])
        exclude_fields = fields_config.get("exclude", [])

        # Build field definitions
        attrs = {"__annotations__": {}}

        for field in model._meta.fields:
            if field.name in exclude_fields:
                continue

            if include_fields and field.name not in include_fields:
                continue

            field_type = self.get_strawberry_field_type(field)
            attrs["__annotations__"][field.name] = field_type

        # Add relationship fields
        relationships = config.get("relationships", {})
        for rel_name, rel_config in relationships.items():
            # Skip non-relationship keys like max_depth, nested_creation, etc.
            if not isinstance(rel_config, dict) or not rel_config.get("include", False):
                continue

            if rel_name in [field.name for field in model._meta.get_fields()]:
                field = model._meta.get_field(rel_name)
                if field.get_internal_type() in ["ForeignKey", "OneToOneField"]:
                    # For now, return the related model type
                    attrs["__annotations__"][rel_name] = strawberry.ID
                elif field.get_internal_type() == "ManyToManyField":
                    attrs["__annotations__"][rel_name] = List[strawberry.ID]

        # Create the output type
        output_type = type(output_name, (), attrs)
        strawberry_type = strawberry.type(output_type)

        self.generated_types[output_name] = strawberry_type
        return strawberry_type

    def generate_complete_schema(self, apps_list: List[str]) -> strawberry.Schema:
        """Generate complete GraphQL schema with all models"""
        try:
            # Load YAML config for the specified apps
            self.config = self._load_yaml_config(apps_list)

            # Find all models in the specified apps
            models_to_include = self.find_all_models(apps_list)

            if not models_to_include:
                logger.warning("No models found in specified apps")
                return self._create_empty_schema()

            # Generate types for all models first
            for model in models_to_include:
                self.generate_input_type(model)
                self.generate_update_input_type(model)
                self.generate_output_type(model)

            # Create the schema with all models
            schema = self._create_schema_with_models(models_to_include)

            logger.info(f"Successfully generated schema for {len(models_to_include)} models")

            return schema

        except Exception as e:
            logger.error(f"Error generating complete schema: {e}")
            return self._create_empty_schema()

    def _create_schema_with_models(self, models_list: List) -> strawberry.Schema:
        """Create schema with all models - DYNAMICALLY GENERATED"""

        # Create Query class with all model queries
        def health_check(self) -> str:
            return "Strawberry CRUD Generator is running"

        query_attrs = {
            "health_check": strawberry.field(health_check),
        }

        # Generate queries for each model
        for model in models_list:
            model_name = model.__name__
            output_type = self.generated_types[f"{model_name}Type"]

            async def get_list(self, limit: int = 10) -> List[output_type]:
                """Get list of {model_name} objects"""
                try:
                    queryset = model.objects.all()[:limit]
                    return await sync_to_async(list)(queryset)
                except Exception as e:
                    logger.error(f"Query error for {model_name}: {e}")
                    return []

            async def get_by_id(self, id: strawberry.ID) -> Optional[output_type]:
                """Get {model_name} by ID"""
                try:
                    return await sync_to_async(model.objects.get)(id=id)
                except Exception as e:
                    logger.error(f"Query error for {model_name}: {e}")
                    return None

            # Add methods to query_attrs
            query_attrs[f"get_{model_name.lower()}_list"] = strawberry.field(get_list)
            query_attrs[f"get_{model_name.lower()}_by_id"] = strawberry.field(get_by_id)

        # Create the Query class
        Query = type("Query", (), query_attrs)
        Query = strawberry.type(Query)

        # Create Mutation class with all model mutations
        def mutation_health_check(self) -> str:
            return "Strawberry CRUD Generator mutations are running"

        mutation_attrs = {
            "health_check": strawberry.field(mutation_health_check),
        }

        # Generate mutations for each model
        for model in models_list:
            model_name = model.__name__
            input_type = self.generated_types[f"{model_name}Input"]
            update_input_type = self.generated_types[f"{model_name}UpdateInput"]
            output_type = self.generated_types[f"{model_name}Type"]

            # Create closures to capture the model
            def make_create_func(model, model_name, input_type, output_type):
                async def create(self, input: input_type) -> output_type:
                    """Create a new {model_name}"""
                    try:
                        # Convert input to model data
                        model_data = {}
                        for field in model._meta.fields:
                            if hasattr(input, field.name):
                                value = getattr(input, field.name)
                                if hasattr(value, "value"):  # Enum value
                                    value = value.value
                                model_data[field.name] = value

                        return await sync_to_async(model.objects.create)(**model_data)
                    except Exception as e:
                        logger.error(f"Create error for {model_name}: {e}")
                        raise Exception(f"Failed to create {model_name}: {str(e)}")

                return create

            def make_update_func(model, model_name, update_input_type, output_type):
                async def update(self, input: update_input_type) -> output_type:
                    """Update a {model_name}"""
                    try:
                        obj = await sync_to_async(model.objects.get)(id=input.id)

                        # Update fields
                        for field in model._meta.fields:
                            if hasattr(input, field.name):
                                value = getattr(input, field.name)
                                if hasattr(value, "value"):  # Enum value
                                    value = value.value
                                setattr(obj, field.name, value)

                        await sync_to_async(obj.save)()
                        return obj
                    except Exception as e:
                        logger.error(f"Update error for {model_name}: {e}")
                        raise Exception(f"Failed to update {model_name}: {str(e)}")

                return update

            def make_delete_func(model, model_name):
                async def delete(self, id: strawberry.ID) -> bool:
                    """Delete a {model_name}"""
                    try:
                        obj = await sync_to_async(model.objects.get)(id=id)
                        await sync_to_async(obj.delete)()
                        return True
                    except Exception as e:
                        logger.error(f"Delete error for {model_name}: {e}")
                        raise Exception(f"Failed to delete {model_name}: {str(e)}")

                return delete

            # Add methods to mutation_attrs
            mutation_attrs[f"create_{model_name.lower()}"] = strawberry.field(
                make_create_func(model, model_name, input_type, output_type),
            )
            mutation_attrs[f"update_{model_name.lower()}"] = strawberry.field(
                make_update_func(model, model_name, update_input_type, output_type),
            )
            mutation_attrs[f"delete_{model_name.lower()}"] = strawberry.field(make_delete_func(model, model_name))

        # Create the Mutation class
        Mutation = type("Mutation", (), mutation_attrs)
        Mutation = strawberry.type(Mutation)

        return strawberry.Schema(query=Query, mutation=Mutation)

    def _create_empty_schema(self) -> strawberry.Schema:
        """Create an empty schema when no models are found"""

        @strawberry.type
        class Query:
            @strawberry.field
            def health_check(self) -> str:
                return "Strawberry CRUD Generator is running"

        @strawberry.type
        class Mutation:
            @strawberry.field
            def noop(self) -> str:
                return "No mutations available"

        return strawberry.Schema(query=Query, mutation=Mutation)
