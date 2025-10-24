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
        import copy

        merged = copy.deepcopy(defaults)

        def deep_merge(d1, d2):
            for key, value in d2.items():
                if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
                    deep_merge(d1[key], value)
                else:
                    # For lists, replace completely (don't merge)
                    if isinstance(value, list):
                        d1[key] = value
                    else:
                        d1[key] = value

        deep_merge(merged, model_config)
        return merged

    def find_all_models(self, apps_list: List[str]) -> List:
        """Find all models in specified apps"""
        apps, _models = get_django_components()
        found_models = []

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

        # Create enum values - use the actual choice values as both keys and values
        enum_values = {}
        for choice_value, choice_label in field.choices:
            # Use the actual choice value as both the key and value
            enum_values[choice_value] = choice_value

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
            return str  # Use string for now, can be improved later
        if field_type in ["DateField"]:
            return str  # Use string for now, can be improved later
        if field_type in ["UUIDField"]:
            return strawberry.ID
        if field_type in ["ForeignKey", "OneToOneField"]:
            # Return the related model type (will be generated later)
            return strawberry.ID  # For now, return ID
        if field_type in ["ManyToManyField"]:
            return List[strawberry.ID]  # For now, return list of IDs

        # Default to string
        return str

    def generate_nested_input_type(self, model, depth: int = 0, max_depth: int = 1, nested_config: dict = None) -> Type:
        """Generate nested input type for a model (for nested creation)

        Args:
            model: Django model class
            depth: Current nesting depth
            max_depth: Maximum nesting depth allowed
            nested_config: Optional nested configuration override (for nested relationships)
        """
        model_name = model.__name__

        # Create a unique name based on the config if provided
        # This prevents caching issues when different relationships have different field configs
        if nested_config and "fields" in nested_config:
            # Create a hash of the fields config to make the type name unique
            fields_config = nested_config.get("fields", {})
            include_fields = fields_config.get("include", [])
            # Use a simplified approach: just add a suffix based on included fields
            if include_fields:
                input_name = f"{model_name}NestedInput_{len(include_fields)}fields"
            else:
                input_name = f"{model_name}NestedInput"
        else:
            input_name = f"{model_name}NestedInput"

        # Prevent infinite recursion
        if depth >= max_depth:
            return None

        # Check cache, but for nested configs, we need to regenerate
        # if the config is different (for now, skip cache for custom configs)
        if not nested_config and input_name in self.generated_types:
            return self.generated_types[input_name]

        # Get model configuration - use nested_config if provided, otherwise use main config
        if nested_config:
            # Merge nested config with main config
            main_config = self.config.get(model_name, {})
            config = {**main_config}

            # Override fields if specified in nested config
            if "fields" in nested_config:
                config["fields"] = nested_config["fields"]

            # Override relationships if specified in nested config
            if "relationships" in nested_config:
                config["relationships"] = nested_config["relationships"]
        else:
            config = self.config.get(model_name, {})

        fields_config = config.get("fields", {})
        include_fields = fields_config.get("include", [])
        exclude_fields = fields_config.get("exclude", [])
        read_only_fields = fields_config.get("read_only", [])

        # Handle "__all__" for include_fields - include all model fields
        if include_fields == "__all__":
            include_fields = [field.name for field in model._meta.fields]

        # Handle "__all__" for exclude_fields - exclude all model fields (rare but possible)
        if exclude_fields == "__all__":
            exclude_fields = [field.name for field in model._meta.fields]

        # Handle "__all__" for read_only_fields - make all fields read-only
        if read_only_fields == "__all__":
            read_only_fields = [field.name for field in model._meta.fields]

        # Build field definitions
        attrs = {"__annotations__": {}}

        # Check if this nested type supports pk lookup (for using existing objects)
        pk_fields = nested_config.get("pk", []) if nested_config else []

        for field in model._meta.fields:
            # Include ID/PK fields if they're in the pk list
            if field.get_internal_type() in ["AutoField", "BigAutoField", "UUIDField"]:
                if field.name in pk_fields or field.name in include_fields:
                    # Include ID field for lookup
                    field_type = self.get_strawberry_field_type(field)
                    attrs["__annotations__"][field.name] = Optional[field_type]
                continue

            # Skip read-only fields
            if field.name in read_only_fields:
                continue

            if field.name in exclude_fields:
                continue

            if include_fields and field.name not in include_fields:
                continue

            field_type = self.get_strawberry_field_type(field)
            attrs["__annotations__"][field.name] = Optional[field_type]

        # Add nested relationships if configured
        relationships = config.get("relationships", {})
        for rel_name, rel_config in relationships.items():
            if not isinstance(rel_config, dict) or not rel_config.get("include", False):
                continue

            if rel_config.get("read_only", False):
                continue

            # Check if nested_creation is boolean or dict
            nested_creation_config = rel_config.get("nested_creation", False)

            # Support both formats:
            # 1. nested_creation: true (simple boolean)
            # 2. nested_creation: { enabled: true, fields: {...}, relationships: {...} }
            if isinstance(nested_creation_config, dict):
                nested_creation_enabled = nested_creation_config.get("enabled", True)
                nested_override = nested_creation_config  # Use the entire config as override
            else:
                nested_creation_enabled = nested_creation_config
                nested_override = None

            if not nested_creation_enabled or depth >= max_depth - 1:
                continue

            # Get the related model
            if rel_name in [field.name for field in model._meta.get_fields()]:
                try:
                    field = model._meta.get_field(rel_name)
                    related_model = field.related_model

                    # Generate nested input type for the related model
                    rel_max_depth = rel_config.get("max_depth", 1)
                    nested_type = self.generate_nested_input_type(
                        related_model,
                        depth + 1,
                        rel_max_depth,
                        nested_override,  # Pass the nested config override
                    )

                    if nested_type:
                        if field.get_internal_type() == "ManyToManyField":
                            attrs["__annotations__"][rel_name] = Optional[List[nested_type]]
                        else:
                            attrs["__annotations__"][rel_name] = Optional[nested_type]
                except Exception as e:
                    logger.warning(f"Could not generate nested type for {rel_name}: {e}")

        # Create the input type
        input_type = type(input_name, (), attrs)
        strawberry_input = strawberry.input(input_type)

        self.generated_types[input_name] = strawberry_input
        return strawberry_input

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
        read_only_fields = fields_config.get("read_only", [])

        # Handle "__all__" for include_fields - include all model fields
        if include_fields == "__all__":
            include_fields = [field.name for field in model._meta.fields]

        # Handle "__all__" for exclude_fields - exclude all model fields (rare but possible)
        if exclude_fields == "__all__":
            exclude_fields = [field.name for field in model._meta.fields]

        # Handle "__all__" for read_only_fields - make all fields read-only
        if read_only_fields == "__all__":
            read_only_fields = [field.name for field in model._meta.fields]

        # Build field definitions
        attrs = {"__annotations__": {}}

        for field in model._meta.fields:
            # Skip auto fields and ID fields for input (they will be generated automatically)
            if field.get_internal_type() in ["AutoField", "BigAutoField", "UUIDField"]:
                continue

            # Skip read-only fields for input
            if field.name in read_only_fields:
                continue

            if field.name in exclude_fields:
                continue

            if include_fields and field.name not in include_fields:
                continue

            field_type = self.get_strawberry_field_type(field)
            attrs["__annotations__"][field.name] = field_type

        # Add relationship fields from YAML configuration
        relationships = config.get("relationships", {})
        for rel_name, rel_config in relationships.items():
            # Skip non-relationship keys like max_depth, nested_creation, etc.
            if not isinstance(rel_config, dict) or not rel_config.get("include", False):
                continue

            # Skip read-only relationships for input
            if rel_config.get("read_only", False):
                continue

            # Check if it's a direct field or reverse relationship
            if rel_name in [field.name for field in model._meta.get_fields()]:
                try:
                    field = model._meta.get_field(rel_name)
                    nested_creation_config = rel_config.get("nested_creation", False)

                    # Support both formats:
                    # 1. nested_creation: true (simple boolean)
                    # 2. nested_creation: { enabled: true, fields: {...}, relationships: {...} }
                    if isinstance(nested_creation_config, dict):
                        nested_creation = nested_creation_config.get("enabled", True)
                        nested_override = nested_creation_config
                    else:
                        nested_creation = nested_creation_config
                        nested_override = None

                    if field.get_internal_type() in ["ForeignKey", "OneToOneField"]:
                        # For ForeignKey/OneToOne, support both ID and nested creation
                        if nested_creation:
                            # Generate nested input type for the related model
                            related_model = field.related_model
                            rel_max_depth = rel_config.get("max_depth", 1)
                            nested_type = self.generate_nested_input_type(
                                related_model,
                                0,
                                rel_max_depth,
                                nested_override,
                            )
                            if nested_type:
                                attrs["__annotations__"][rel_name] = Optional[nested_type]
                            else:
                                attrs["__annotations__"][rel_name] = Optional[strawberry.ID]
                        else:
                            attrs["__annotations__"][rel_name] = Optional[strawberry.ID]
                    elif field.get_internal_type() == "ManyToManyField":
                        # For ManyToMany, support both list of IDs and nested creation
                        if nested_creation:
                            # Generate nested input type for the related model
                            related_model = field.related_model
                            rel_max_depth = rel_config.get("max_depth", 1)
                            nested_type = self.generate_nested_input_type(
                                related_model,
                                0,
                                rel_max_depth,
                                nested_override,
                            )
                            if nested_type:
                                attrs["__annotations__"][rel_name] = Optional[List[nested_type]]
                            else:
                                attrs["__annotations__"][rel_name] = Optional[List[strawberry.ID]]
                        else:
                            attrs["__annotations__"][rel_name] = Optional[List[strawberry.ID]]
                except Exception as e:
                    # It's a reverse relationship, treat as ManyToMany for now
                    logger.warning(f"Could not process relationship {rel_name}: {e}")
                    nested_creation = rel_config.get("nested_creation", False)
                    if nested_creation:
                        attrs["__annotations__"][rel_name] = Optional[strawberry.scalars.JSON]
                    else:
                        attrs["__annotations__"][rel_name] = Optional[List[strawberry.ID]]
            else:
                # It's a reverse relationship, treat as ManyToMany for now
                nested_creation = rel_config.get("nested_creation", False)
                if nested_creation:
                    attrs["__annotations__"][rel_name] = Optional[strawberry.scalars.JSON]
                else:
                    attrs["__annotations__"][rel_name] = Optional[List[strawberry.ID]]

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
        read_only_fields = fields_config.get("read_only", [])

        # Handle "__all__" for include_fields - include all model fields
        if include_fields == "__all__":
            include_fields = [field.name for field in model._meta.fields]

        # Handle "__all__" for exclude_fields - exclude all model fields (rare but possible)
        if exclude_fields == "__all__":
            exclude_fields = [field.name for field in model._meta.fields]

        # Handle "__all__" for read_only_fields - make all fields read-only
        if read_only_fields == "__all__":
            read_only_fields = [field.name for field in model._meta.fields]

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

            # Skip read-only fields for update input
            if field.name in read_only_fields:
                continue

            field_type = self.get_strawberry_field_type(field)
            attrs["__annotations__"][field.name] = field_type

        # Add relationship fields from YAML configuration
        relationships = config.get("relationships", {})
        for rel_name, rel_config in relationships.items():
            # Skip non-relationship keys like max_depth, nested_creation, etc.
            if not isinstance(rel_config, dict) or not rel_config.get("include", False):
                continue

            # Skip read-only relationships for input
            if rel_config.get("read_only", False):
                continue

            # Check if it's a direct field or reverse relationship
            if rel_name in [field.name for field in model._meta.get_fields()]:
                try:
                    field = model._meta.get_field(rel_name)
                    nested_updates = rel_config.get("nested_updates", False)

                    if field.get_internal_type() in ["ForeignKey", "OneToOneField"]:
                        # For ForeignKey/OneToOne, support both ID and nested updates
                        if nested_updates:
                            # Use JSON scalar to accept both ID string or nested object
                            attrs["__annotations__"][rel_name] = Optional[strawberry.scalars.JSON]
                        else:
                            attrs["__annotations__"][rel_name] = Optional[strawberry.ID]
                    elif field.get_internal_type() == "ManyToManyField":
                        # For ManyToMany, support both list of IDs and nested updates
                        if nested_updates:
                            attrs["__annotations__"][rel_name] = Optional[strawberry.scalars.JSON]
                        else:
                            attrs["__annotations__"][rel_name] = Optional[List[strawberry.ID]]
                except Exception:
                    # It's a reverse relationship, treat as ManyToMany for now
                    nested_updates = rel_config.get("nested_updates", False)
                    if nested_updates:
                        attrs["__annotations__"][rel_name] = Optional[strawberry.scalars.JSON]
                    else:
                        attrs["__annotations__"][rel_name] = Optional[List[strawberry.ID]]
            else:
                # It's a reverse relationship, treat as ManyToMany for now
                nested_updates = rel_config.get("nested_updates", False)
                if nested_updates:
                    attrs["__annotations__"][rel_name] = Optional[strawberry.scalars.JSON]
                else:
                    attrs["__annotations__"][rel_name] = Optional[List[strawberry.ID]]

        # Create the input type
        input_type = type(input_name, (), attrs)
        strawberry_input = strawberry.input(input_type)

        self.generated_types[input_name] = strawberry_input
        return strawberry_input

    def _detect_circular_references(self, models_to_include, type_defs):
        """
        Detect circular reference patterns in relationships.
        Returns a set of (model_name, related_model_name) tuples that would create circles.

        Algorithm:
        1. Build a directed graph of relationships
        2. Find all cycles in the graph
        3. For each cycle, mark one edge to skip (prefer reverse relationships)
        """
        # Build relationship graph
        graph = {}  # {model_name: {related_model_name: (rel_name, is_reverse)}}

        for model in models_to_include:
            model_name = model.__name__
            type_def = type_defs.get(model_name)
            if not type_def:
                continue

            graph[model_name] = {}
            relationships = type_def.get("_relationships", {})

            for rel_name, rel_info in relationships.items():
                related_model_name = rel_info["related_model_name"]
                field_class = rel_info["field_class"]
                is_reverse = field_class in ["ManyToOneRel", "ManyToManyRel", "OneToOneRel"]
                graph[model_name][related_model_name] = (rel_name, is_reverse)

        # Find circular patterns using DFS
        circular_edges = set()

        def find_cycles(node, path, visited):
            """DFS to find cycles"""
            if node in path:
                # Found a cycle! Mark the edge that closes the loop
                cycle_start = path.index(node)
                cycle = path[cycle_start:]

                # Choose which edge to remove (prefer reverse relationships)
                # Find the "best" edge to cut (prefer reverse relationships)
                best_cut = None
                best_score = -1

                for i in range(len(cycle)):
                    from_node = cycle[i]
                    to_node = cycle[(i + 1) % len(cycle)]

                    if to_node in graph.get(from_node, {}):
                        _, is_reverse = graph[from_node][to_node]
                        # Prefer cutting reverse relationships (higher score)
                        score = 1 if is_reverse else 0
                        if score > best_score:
                            best_score = score
                            best_cut = (from_node, to_node)

                if best_cut:
                    circular_edges.add(best_cut)
                    logger.info(f"🔍 Detected circular pattern: {" -> ".join(cycle + [node])}")
                    logger.info(f"   Will skip: {best_cut[0]}.{graph[best_cut[0]][best_cut[1]][0]} -> {best_cut[1]}")

                return

            if node in visited:
                return

            visited.add(node)
            path.append(node)

            for related_node in graph.get(node, {}):
                find_cycles(related_node, path.copy(), visited)

        # Run cycle detection for all nodes
        for start_node in graph:
            find_cycles(start_node, [], set())

        return circular_edges

    def _build_output_type_def(self, model, include_relationships=False):
        """Build type definition dict (annotations) for output type"""
        model_name = model.__name__

        # Get model configuration
        config = self.config.get(model_name, {})
        fields_config = config.get("fields", {})
        include_fields = fields_config.get("include", [])
        exclude_fields = fields_config.get("exclude", [])

        # Handle "__all__"
        if include_fields == "__all__":
            include_fields = [field.name for field in model._meta.fields]
        if exclude_fields == "__all__":
            exclude_fields = [field.name for field in model._meta.fields]

        # Build field definitions
        attrs = {"__annotations__": {}, "_model": model}

        # Add regular fields
        for field in model._meta.fields:
            if field.name in exclude_fields:
                continue
            if include_fields and field.name not in include_fields:
                continue
            field_type = self.get_strawberry_field_type(field)
            attrs["__annotations__"][field.name] = field_type

        return attrs

    def _add_relationships_to_type_def(self, model, type_def, all_type_defs):
        """Add relationship annotations to a type definition"""
        model_name = model.__name__

        # Get model configuration
        config = self.config.get(model_name, {})
        relationships = config.get("relationships", {})

        # Add relationship fields
        for rel_name, rel_config in relationships.items():
            if not isinstance(rel_config, dict) or not rel_config.get("include", False):
                continue

            if rel_name in [field.name for field in model._meta.get_fields()]:
                try:
                    field = model._meta.get_field(rel_name)
                    related_model = field.related_model
                    related_model_name = related_model.__name__

                    # Check if the related type definition exists
                    related_type_def = all_type_defs.get(related_model_name)
                    if not related_type_def:
                        logger.warning(f"Related model {related_model_name} not found in type defs")
                        continue

                    # We need to use string annotations (forward references)
                    # because the types don't exist yet
                    related_output_name = f"{related_model_name}Type"

                    # Check field class
                    field_class_name = field.__class__.__name__

                    # Add annotation based on relationship type
                    # Use string annotations for forward reference
                    if field_class_name in ["ManyToOneRel", "ManyToManyRel", "OneToOneRel"]:
                        # Store as string - will be resolved by Strawberry
                        type_def["__annotations__"][rel_name] = f'List["{related_output_name}"]'
                    else:
                        try:
                            field_type = field.get_internal_type()
                        except AttributeError:
                            field_type = None

                        if field_type in ["ForeignKey", "OneToOneField"]:
                            type_def["__annotations__"][rel_name] = f'Optional["{related_output_name}"]'
                        elif field_type == "ManyToManyField":
                            type_def["__annotations__"][rel_name] = f'List["{related_output_name}"]'

                except Exception as e:
                    logger.warning(f"Could not add relationship {rel_name}: {e}")

    def _generate_output_type_with_relationships(self, model, all_models) -> Type:
        """Generate output type with relationships using forward references"""
        model_name = model.__name__
        output_name = f"{model_name}Type"

        # Check if already generated
        if output_name in self.generated_types:
            return self.generated_types[output_name]

        # Mark as being generated (to prevent infinite recursion)
        if not hasattr(self, "_generating_types"):
            self._generating_types = set()

        if output_name in self._generating_types:
            # We're already generating this type (circular reference detected)
            # Create a placeholder type that will be filled in later
            logger.info(f"Circular reference detected for {output_name}, using placeholder")
            # Return None to indicate we're in a circular reference
            return None

        self._generating_types.add(output_name)

        # Get model configuration
        config = self.config.get(model_name, {})
        fields_config = config.get("fields", {})
        include_fields = fields_config.get("include", [])
        exclude_fields = fields_config.get("exclude", [])
        relationships = config.get("relationships", {})

        # Handle "__all__"
        if include_fields == "__all__":
            include_fields = [field.name for field in model._meta.fields]
        if exclude_fields == "__all__":
            exclude_fields = [field.name for field in model._meta.fields]

        # Build field definitions
        attrs = {"__annotations__": {}}

        # Add regular fields
        for field in model._meta.fields:
            if field.name in exclude_fields:
                continue
            if include_fields and field.name not in include_fields:
                continue
            field_type = self.get_strawberry_field_type(field)
            attrs["__annotations__"][field.name] = field_type

        # Add relationship fields
        for rel_name, rel_config in relationships.items():
            if not isinstance(rel_config, dict) or not rel_config.get("include", False):
                continue

            if rel_name in [field.name for field in model._meta.get_fields()]:
                try:
                    field = model._meta.get_field(rel_name)
                    related_model = field.related_model
                    related_model_name = related_model.__name__
                    related_output_name = f"{related_model_name}Type"

                    # Check if the related type exists, if not, recursively generate it
                    if related_output_name not in self.generated_types:
                        result = self._generate_output_type_with_relationships(related_model, all_models)
                        # If result is None, we hit a circular reference
                        # Skip this relationship for now - it will be handled later
                        if result is None:
                            logger.info(f"Skipping circular relationship {rel_name} in {model_name}")
                            continue

                    related_type = self.generated_types.get(related_output_name)

                    if not related_type:
                        logger.warning(f"Could not generate {related_output_name}")
                        continue

                    # Check field class
                    field_class_name = field.__class__.__name__

                    if field_class_name in ["ManyToOneRel", "ManyToManyRel", "OneToOneRel"]:
                        attrs["__annotations__"][rel_name] = List[related_type]
                    else:
                        field_type = field.get_internal_type()
                        if field_type in ["ForeignKey", "OneToOneField"]:
                            attrs["__annotations__"][rel_name] = Optional[related_type]
                        elif field_type == "ManyToManyField":
                            attrs["__annotations__"][rel_name] = List[related_type]
                except Exception as e:
                    logger.warning(f"Could not add relationship {rel_name}: {e}")

        # Create the output type
        output_type = type(output_name, (), attrs)
        strawberry_type = strawberry.type(output_type)

        self.generated_types[output_name] = strawberry_type

        # Remove from generating set
        self._generating_types.discard(output_name)

        return strawberry_type

    def _generate_output_type_base(self, model) -> Type:
        """Generate Strawberry output type for a model WITHOUT relationships (to avoid circular refs)"""
        model_name = model.__name__
        output_name = f"{model_name}Type"

        if output_name in self.generated_types:
            return self.generated_types[output_name]

        # Ensure config is loaded
        if not self.config:
            self.config = self._load_yaml_config(self.apps_list)

        # Get model configuration
        config = self.config.get(model_name, {})
        fields_config = config.get("fields", {})
        include_fields = fields_config.get("include", [])
        exclude_fields = fields_config.get("exclude", [])

        # Handle "__all__" for include_fields - include all model fields
        if include_fields == "__all__":
            include_fields = [field.name for field in model._meta.fields]

        # Handle "__all__" for exclude_fields - exclude all model fields (rare but possible)
        if exclude_fields == "__all__":
            exclude_fields = [field.name for field in model._meta.fields]

        # Build field definitions (only regular fields, no relationships yet)
        attrs = {"__annotations__": {}}

        for field in model._meta.fields:
            if field.name in exclude_fields:
                continue

            if include_fields and field.name not in include_fields:
                continue

            field_type = self.get_strawberry_field_type(field)
            attrs["__annotations__"][field.name] = field_type

        # Create the output type (without relationships)
        output_type = type(output_name, (), attrs)
        strawberry_type = strawberry.type(output_type)

        self.generated_types[output_name] = strawberry_type
        return strawberry_type

    def _add_relationships_to_output_type(self, model):
        """Regenerate output type WITH relationships (now that all types exist)"""
        model_name = model.__name__
        output_name = f"{model_name}Type"

        # Get the base type (without relationships)
        base_type = self.generated_types.get(output_name)
        if not base_type:
            logger.warning(f"Cannot add relationships to {output_name} - base type not found")
            return

        # Get model configuration
        config = self.config.get(model_name, {})
        fields_config = config.get("fields", {})
        include_fields = fields_config.get("include", [])
        exclude_fields = fields_config.get("exclude", [])
        relationships = config.get("relationships", {})

        # Handle "__all__" for include_fields
        if include_fields == "__all__":
            include_fields = [field.name for field in model._meta.fields]

        # Handle "__all__" for exclude_fields
        if exclude_fields == "__all__":
            exclude_fields = [field.name for field in model._meta.fields]

        # Rebuild the type with relationships
        attrs = {"__annotations__": {}}

        # Copy regular fields from the base type
        for field in model._meta.fields:
            if field.name in exclude_fields:
                continue
            if include_fields and field.name not in include_fields:
                continue
            field_type = self.get_strawberry_field_type(field)
            attrs["__annotations__"][field.name] = field_type

        # Add relationship fields
        for rel_name, rel_config in relationships.items():
            # Skip non-relationship keys
            if not isinstance(rel_config, dict) or not rel_config.get("include", False):
                continue

            # Check if it's a direct field or reverse relationship
            if rel_name in [field.name for field in model._meta.get_fields()]:
                try:
                    field = model._meta.get_field(rel_name)
                    related_model = field.related_model
                    related_model_name = related_model.__name__
                    related_output_name = f"{related_model_name}Type"

                    # Get the related type (it should already be generated)
                    related_type = self.generated_types.get(related_output_name)
                    if not related_type:
                        logger.warning(f"Related type {related_output_name} not found for {rel_name}")
                        continue

                    # Check if it's a reverse relationship first (by checking the class name)
                    field_class_name = field.__class__.__name__

                    if field_class_name in ["ManyToOneRel", "ManyToManyRel", "OneToOneRel"]:
                        # It's a reverse relationship - return list of nested objects
                        attrs["__annotations__"][rel_name] = List[related_type]
                    else:
                        # It's a forward relationship - check the field type
                        field_type = field.get_internal_type()

                        if field_type in ["ForeignKey", "OneToOneField"]:
                            # Return single nested object
                            attrs["__annotations__"][rel_name] = Optional[related_type]
                        elif field_type == "ManyToManyField":
                            # Return list of nested objects
                            attrs["__annotations__"][rel_name] = List[related_type]
                except Exception as e:
                    logger.warning(f"Could not add relationship {rel_name} to {output_name}: {e}")

        # Recreate the output type with relationships
        output_type = type(output_name, (), attrs)
        strawberry_type = strawberry.type(output_type)

        # Replace the existing type
        self.generated_types[output_name] = strawberry_type

    def generate_complete_schema(self, apps_list: List[str]) -> strawberry.Schema:
        """Generate complete GraphQL schema with all models"""
        try:
            # Load YAML config for the specified apps only if not already loaded
            if not self.config:
                self.config = self._load_yaml_config(apps_list)
                self.apps_list = apps_list

            # Find all models in the specified apps
            models_to_include = self.find_all_models(apps_list)

            if not models_to_include:
                logger.warning("No models found in specified apps")
                return self._create_empty_schema()

            # Generate input/update types first (these don't have circular ref issues)
            for model in models_to_include:
                self.generate_input_type(model)
                self.generate_update_input_type(model)

            # Two-pass approach for output types:
            # Pass 1: Generate all base types WITHOUT relationships
            type_defs = {}  # Store type definitions before wrapping with strawberry
            for model in models_to_include:
                type_defs[model.__name__] = self._build_output_type_def(model, include_relationships=False)

            # Pass 2: Add relationships to type definitions (now all types are defined)
            for model in models_to_include:
                model_name = model.__name__
                type_def = type_defs[model_name]

                # Get relationships config
                config = self.config.get(model_name, {})
                relationships = config.get("relationships", {})

                # Add relationship fields to the type definition
                for rel_name, rel_config in relationships.items():
                    if not isinstance(rel_config, dict) or not rel_config.get("include", False):
                        continue

                    if rel_name in [field.name for field in model._meta.get_fields()]:
                        try:
                            field = model._meta.get_field(rel_name)
                            related_model = field.related_model
                            related_model_name = related_model.__name__

                            # Check if related model has a type def
                            if related_model_name not in type_defs:
                                continue

                            # Store relationship info (will be resolved in Pass 3)
                            if "_relationships" not in type_def:
                                type_def["_relationships"] = {}

                            # Store relationship metadata
                            field_class_name = field.__class__.__name__
                            try:
                                field_type = field.get_internal_type()
                            except AttributeError:
                                field_type = None

                            type_def["_relationships"][rel_name] = {
                                "related_model_name": related_model_name,
                                "field_class": field_class_name,
                                "field_type": field_type,
                            }
                        except Exception as e:
                            logger.warning(f"Could not prepare relationship {rel_name}: {e}")

            # Pass 3: Create all types at once WITH relationships
            # We need to create placeholder types first (just Python classes, not Strawberry types)
            # so they can reference each other
            python_types = {}
            for model_name, type_def in type_defs.items():
                output_name = f"{model_name}Type"
                # Build complete annotations including relationships
                attrs = {"__annotations__": {}}

                # Copy regular field annotations
                for key, value in type_def.get("__annotations__", {}).items():
                    attrs["__annotations__"][key] = value

                # Create the Python type (not Strawberry type yet)
                python_type = type(output_name, (), attrs)
                python_types[output_name] = (python_type, attrs, type_def)

            # Now add relationships to annotations (all Python types exist for reference)
            # But detect and prevent circular patterns (A -> B -> A)
            circular_refs = self._detect_circular_references(models_to_include, type_defs)

            for model in models_to_include:
                model_name = model.__name__
                output_name = f"{model_name}Type"
                python_type, attrs, type_def = python_types[output_name]

                # Add relationship annotations
                relationships = type_def.get("_relationships", {})
                for rel_name, rel_info in relationships.items():
                    related_model_name = rel_info["related_model_name"]
                    related_output_name = f"{related_model_name}Type"

                    # Check if this would create a circular reference
                    if (model_name, related_model_name) in circular_refs:
                        logger.info(
                            f"⚠️  Skipping circular relationship: {model_name}.{rel_name} -> {related_model_name} (would create infinite nesting)"
                        )
                        continue

                    # Get the related Python type (not Strawberry type yet)
                    related_python_type, _, _ = python_types.get(related_output_name, (None, None, None))

                    if not related_python_type:
                        continue

                    field_class = rel_info["field_class"]
                    field_type = rel_info["field_type"]

                    # Add the relationship annotation using the Python type
                    if field_class in ["ManyToOneRel", "ManyToManyRel", "OneToOneRel"]:
                        attrs["__annotations__"][rel_name] = List[related_python_type]
                    elif field_type in ["ForeignKey", "OneToOneField"]:
                        attrs["__annotations__"][rel_name] = Optional[related_python_type]
                    elif field_type == "ManyToManyField":
                        attrs["__annotations__"][rel_name] = List[related_python_type]

                # Update the python type's annotations
                python_type.__annotations__.update(attrs["__annotations__"])

            # Pass 4: Convert Python types to Strawberry types (only once!)
            for output_name, (python_type, attrs, type_def) in python_types.items():
                strawberry_type = strawberry.type(python_type)
                self.generated_types[output_name] = strawberry_type

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
            def make_create_func(model, model_name, input_type, output_type, generator):
                async def create(self, input: input_type) -> output_type:
                    """Create a new {model_name}"""
                    try:
                        # Convert input to model data
                        model_data = {}
                        relationship_data = {}

                        # Process regular fields
                        for field in model._meta.fields:
                            if hasattr(input, field.name):
                                value = getattr(input, field.name)
                                if hasattr(value, "value"):  # Enum value
                                    value = value.value
                                model_data[field.name] = value

                        # Process relationship fields
                        config = generator.config.get(model_name, {})
                        relationships = config.get("relationships", {})
                        for rel_name, rel_config in relationships.items():
                            if not isinstance(rel_config, dict) or not rel_config.get("include", False):
                                continue
                            if hasattr(input, rel_name):
                                value = getattr(input, rel_name)
                                if value is not None:
                                    relationship_data[rel_name] = value

                        # Create the object
                        obj = await sync_to_async(model.objects.create)(**model_data)

                        # Handle relationships after creation
                        for rel_name, rel_value in relationship_data.items():
                            if rel_name in [field.name for field in model._meta.get_fields()]:
                                try:
                                    field = model._meta.get_field(rel_name)
                                    rel_config = relationships.get(rel_name, {})
                                    nested_creation = rel_config.get("nested_creation", False)

                                    if field.get_internal_type() == "ManyToManyField":
                                        # Handle ManyToMany relationships
                                        if isinstance(rel_value, list):
                                            related_objects = []
                                            for item in rel_value:
                                                if isinstance(item, dict) and nested_creation:
                                                    # Check if 'id' is provided in the dict (use existing object)
                                                    if "id" in item and item["id"]:
                                                        # Fetch existing object by ID
                                                        related_obj = await sync_to_async(
                                                            field.related_model.objects.get,
                                                        )(
                                                            id=item["id"],
                                                        )
                                                    else:
                                                        # Nested creation - create the related object
                                                        # Remove id from the data if it's None
                                                        create_data = {k: v for k, v in item.items() if k != "id"}
                                                        related_obj = await sync_to_async(
                                                            field.related_model.objects.create,
                                                        )(**create_data)
                                                    related_objects.append(related_obj)
                                                elif isinstance(item, str):
                                                    # ID reference - fetch existing object
                                                    related_obj = await sync_to_async(field.related_model.objects.get)(
                                                        id=item,
                                                    )
                                                    related_objects.append(related_obj)
                                            await sync_to_async(obj.__getattribute__(rel_name).set)(related_objects)
                                    else:
                                        # Handle ForeignKey/OneToOne relationships
                                        if rel_value:
                                            if isinstance(rel_value, dict) and nested_creation:
                                                # Check if 'id' is provided in the dict (use existing object)
                                                if "id" in rel_value and rel_value["id"]:
                                                    # Fetch existing object by ID
                                                    related_obj = await sync_to_async(field.related_model.objects.get)(
                                                        id=rel_value["id"],
                                                    )
                                                else:
                                                    # Nested creation - create the related object
                                                    # Remove id from the data if it's None
                                                    create_data = {k: v for k, v in rel_value.items() if k != "id"}
                                                    related_obj = await sync_to_async(
                                                        field.related_model.objects.create,
                                                    )(
                                                        **create_data,
                                                    )
                                                setattr(obj, rel_name, related_obj)
                                            elif isinstance(rel_value, str):
                                                # ID reference - fetch existing object
                                                related_obj = await sync_to_async(field.related_model.objects.get)(
                                                    id=rel_value,
                                                )
                                                setattr(obj, rel_name, related_obj)
                                except Exception as rel_e:
                                    logger.warning(f"Could not set relationship {rel_name}: {rel_e}")

                        # Save if we made changes to relationships
                        if relationship_data:
                            await sync_to_async(obj.save)()

                        return await generator._convert_to_graphql_type(obj, output_type)
                    except Exception as e:
                        logger.error(f"Create error for {model_name}: {e}")
                        raise Exception(f"Failed to create {model_name}: {str(e)}")

                return create

            def make_update_func(model, model_name, update_input_type, output_type, generator):
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
                        return await generator._convert_to_graphql_type(obj, output_type)
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
                make_create_func(model, model_name, input_type, output_type, self),
            )
            mutation_attrs[f"update_{model_name.lower()}"] = strawberry.field(
                make_update_func(model, model_name, update_input_type, output_type, self),
            )
            mutation_attrs[f"delete_{model_name.lower()}"] = strawberry.field(make_delete_func(model, model_name))

        # Create the Mutation class
        Mutation = type("Mutation", (), mutation_attrs)
        Mutation = strawberry.type(Mutation)

        return strawberry.Schema(query=Query, mutation=Mutation)

    async def _convert_to_graphql_type(self, instance, output_type):
        """Convert Django model instance to GraphQL type with proper enum and relationship handling"""
        attrs = {}

        # Get the output type annotations to know which fields to include
        output_annotations = output_type.__annotations__

        # Handle regular fields
        for field in instance._meta.fields:
            if field.name not in output_annotations:
                continue

            value = getattr(instance, field.name)

            # Handle enum fields - return the actual choice value for GraphQL
            if hasattr(field, "choices") and field.choices:
                # Return the actual choice value (not the display label)
                attrs[field.name] = value
            else:
                attrs[field.name] = value

        # Handle relationships - return full nested objects
        config = self.config.get(instance.__class__.__name__, {})
        relationships = config.get("relationships", {})

        for rel_name, rel_config in relationships.items():
            if not isinstance(rel_config, dict) or not rel_config.get("include", False):
                continue

            if rel_name not in output_annotations:
                continue

            if hasattr(instance, rel_name):
                related_obj = getattr(instance, rel_name)
                if related_obj:
                    if hasattr(related_obj, "all"):  # ManyToMany or reverse ForeignKey
                        # Use sync_to_async for the queryset evaluation
                        related_objects = await sync_to_async(list)(related_obj.all())

                        # Get the related model's output type
                        if related_objects:
                            related_model = related_objects[0].__class__
                            related_output_type_name = f"{related_model.__name__}Type"
                            related_output_type = self.generated_types.get(related_output_type_name)

                            if related_output_type:
                                # Recursively convert each related object
                                nested_objects = []
                                for obj in related_objects:
                                    nested_obj = await self._convert_to_graphql_type(obj, related_output_type)
                                    nested_objects.append(nested_obj)
                                attrs[rel_name] = nested_objects
                            else:
                                # Fallback to IDs if type not found
                                attrs[rel_name] = [str(obj.id) for obj in related_objects]
                        else:
                            attrs[rel_name] = []
                    elif hasattr(related_obj, "id"):  # ForeignKey, OneToOne
                        # Get the related model's output type
                        related_model = related_obj.__class__
                        related_output_type_name = f"{related_model.__name__}Type"
                        related_output_type = self.generated_types.get(related_output_type_name)

                        if related_output_type:
                            # Recursively convert the related object
                            attrs[rel_name] = await self._convert_to_graphql_type(related_obj, related_output_type)
                        else:
                            # Fallback to ID if type not found
                            attrs[rel_name] = str(related_obj.id)
                else:
                    attrs[rel_name] = None

        return output_type(**attrs)

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
