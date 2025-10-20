# GraphQL Generator - Implementation Guide

This document provides detailed technical information about the GraphQL Generator implementation, architecture, and internal workings.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
- [Implementation Details](#implementation-details)
- [Type Generation](#type-generation)
- [Relationship Handling](#relationship-handling)
- [Async Operations](#async-operations)
- [Configuration System](#configuration-system)
- [Error Handling](#error-handling)
- [Performance Considerations](#performance-considerations)
- [Extension Points](#extension-points)

## Architecture Overview

The GraphQL Generator follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    GraphQL Generator                       │
├─────────────────────────────────────────────────────────────┤
│  StrawberryCRUDGenerator (Main Controller)                 │
├─────────────────────────────────────────────────────────────┤
│  Configuration Layer                                        │
│  ├── YAML Loader                                           │
│  ├── Default Merger                                        │
│  └── Model Discovery                                       │
├─────────────────────────────────────────────────────────────┤
│  Type Generation Layer                                     │
│  ├── Input Type Generator                                  │
│  ├── Output Type Generator                                 │
│  ├── Update Type Generator                                 │
│  └── Enum Generator                                        │
├─────────────────────────────────────────────────────────────┤
│  Schema Generation Layer                                   │
│  ├── Query Generator                                       │
│  ├── Mutation Generator                                    │
│  └── Schema Builder                                        │
├─────────────────────────────────────────────────────────────┤
│  Runtime Layer                                             │
│  ├── Async Operations                                      │
│  ├── Relationship Resolution                               │
│  └── Type Conversion                                       │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. StrawberryCRUDGenerator

The main class that orchestrates the entire generation process.

```python
class StrawberryCRUDGenerator:
    def __init__(self, apps_list: List[str] = None):
        self.apps_list = apps_list or []
        self.config = self._load_yaml_config(self.apps_list) if self.apps_list else {}
        self.generated_types = {}
        self.generated_enums = {}
```

**Key Responsibilities:**
- Configuration management
- Type generation coordination
- Schema assembly
- Runtime operation handling

### 2. Configuration System

Handles YAML configuration loading and merging:

```python
def _load_yaml_config(self, apps_list: List[str]) -> Dict[str, Any]:
    """Load YAML configuration from each app's gql_config folder"""
    all_configs = {}
    
    for app_name in apps_list:
        app_config_dir = Path(__file__).parent.parent.parent / "core" / app_name / "gql_config"
        
        # Load defaults first
        defaults = self._load_defaults(app_config_dir)
        
        # Try single models.yml file first
        single_config_path = app_config_dir / "models.yml"
        if single_config_path.exists():
            # Process single file
        else:
            # Process individual model files
```

**Features:**
- Default inheritance
- Multiple configuration formats
- Deep merging
- Validation

### 3. Type Generation System

Dynamically generates Strawberry GraphQL types:

```python
def generate_output_type(self, model) -> Type:
    """Generate Strawberry output type for a model"""
    # Build field definitions
    attrs = {"__annotations__": {}}
    
    for field in model._meta.fields:
        if field.name not in output_annotations:
            continue
        
        field_type = self.get_strawberry_field_type(field)
        attrs["__annotations__"][field.name] = field_type
    
    # Add relationship fields
    # ... relationship handling ...
    
    # Create the output type
    output_type = type(output_name, (), attrs)
    strawberry_type = strawberry.type(output_type)
```

## Implementation Details

### Type Generation Process

#### 1. Field Type Mapping

The generator maps Django field types to Strawberry GraphQL types:

```python
def get_strawberry_field_type(self, field) -> Any:
    field_type = field.get_internal_type()
    
    # Handle choice fields
    if hasattr(field, "choices") and field.choices:
        enum_type = self.generate_enum_from_choices(field)
        if enum_type:
            return enum_type
    
    # Map Django field types to Strawberry types
    type_mapping = {
        "CharField": str,
        "TextField": str,
        "EmailField": str,
        "URLField": str,
        "IntegerField": int,
        "BigIntegerField": int,
        "SmallIntegerField": int,
        "FloatField": float,
        "DecimalField": float,
        "BooleanField": bool,
        "DateTimeField": strawberry.auto,
        "DateField": strawberry.auto,
        "UUIDField": strawberry.ID,
        "ForeignKey": strawberry.ID,
        "OneToOneField": strawberry.ID,
        "ManyToManyField": List[strawberry.ID],
    }
    
    return type_mapping.get(field_type, str)
```

#### 2. Enum Generation

Converts Django TextChoices to GraphQL enums:

```python
def generate_enum_from_choices(self, field) -> Optional[Type[Enum]]:
    if not hasattr(field, "choices") or not field.choices:
        return None

    enum_name = f"{field.model.__name__}{field.name.title()}Enum"
    
    if enum_name in self.generated_enums:
        return self.generated_enums[enum_name]

    # Create enum values - use actual choice values
    enum_values = {}
    for choice_value, choice_label in field.choices:
        enum_values[choice_value] = choice_value

    # Create the enum class
    enum_class = Enum(enum_name, enum_values)
    strawberry_enum = strawberry.enum(enum_class)
    
    self.generated_enums[enum_name] = strawberry_enum
    return strawberry_enum
```

#### 3. Dynamic Type Creation

Uses Python's `type()` function to create types dynamically:

```python
# Create input type
input_type = type(input_name, (), attrs)
strawberry_input = strawberry.input(input_type)

# Create output type
output_type = type(output_name, (), attrs)
strawberry_type = strawberry.type(output_type)
```

### Relationship Handling

#### 1. Relationship Detection

The generator identifies relationships by checking Django model fields:

```python
# Check if it's a direct field or reverse relationship
if rel_name in [field.name for field in model._meta.get_fields()]:
    try:
        field = model._meta.get_field(rel_name)
        # Check if it's a reverse relationship
        if hasattr(field, 'related_model'):
            # It's a reverse relationship
            attrs["__annotations__"][rel_name] = List[strawberry.ID]
        elif field.get_internal_type() in ["ForeignKey", "OneToOneField"]:
            # Direct relationship
            attrs["__annotations__"][rel_name] = strawberry.ID
        elif field.get_internal_type() == "ManyToManyField":
            # Many-to-many relationship
            attrs["__annotations__"][rel_name] = List[strawberry.ID]
    except Exception:
        # Fallback for reverse relationships
        attrs["__annotations__"][rel_name] = List[strawberry.ID]
```

#### 2. Relationship Resolution

At runtime, relationships are resolved to actual data:

```python
async def _convert_to_graphql_type(self, instance, output_type):
    """Convert Django model instance to GraphQL type"""
    attrs = {}
    
    # Handle regular fields
    for field in instance._meta.fields:
        if field.name not in output_annotations:
            continue
        
        value = getattr(instance, field.name)
        
        # Handle enum fields
        if hasattr(field, "choices") and field.choices:
            attrs[field.name] = value  # Use actual choice value
        else:
            attrs[field.name] = value
    
    # Handle relationships
    for rel_name, rel_config in relationships.items():
        if not isinstance(rel_config, dict) or not rel_config.get("include", False):
            continue
        
        if hasattr(instance, rel_name):
            related_obj = getattr(instance, rel_name)
            if related_obj:
                if hasattr(related_obj, "all"):  # ManyToMany
                    related_objects = await sync_to_async(list)(related_obj.all())
                    attrs[rel_name] = [str(obj.id) for obj in related_objects]
                elif hasattr(related_obj, "id"):  # ForeignKey, OneToOne
                    attrs[rel_name] = str(related_obj.id)
            else:
                attrs[rel_name] = None
    
    return output_type(**attrs)
```

### Async Operations

#### 1. Async Mutation Functions

All mutations are async to handle database operations properly:

```python
def make_create_func(model, model_name, input_type, output_type, generator):
    async def create(self, input: input_type) -> output_type:
        try:
            # Convert input to model data
            model_data = {}
            for field in model._meta.fields:
                if hasattr(input, field.name):
                    value = getattr(input, field.name)
                    if hasattr(value, "value"):  # Enum value
                        value = value.value
                    model_data[field.name] = value
            
            # Create object
            obj = await sync_to_async(model.objects.create)(**model_data)
            return await generator._convert_to_graphql_type(obj, output_type)
        except Exception as e:
            logger.error(f"Create error for {model_name}: {e}")
            raise Exception(f"Failed to create {model_name}: {str(e)}")
    
    return create
```

#### 2. Async Query Functions

Queries are also async for consistency:

```python
async def get_list(self, limit: int = 10) -> List[output_type]:
    try:
        queryset = model.objects.all()[:limit]
        return await sync_to_async(list)(queryset)
    except Exception as e:
        logger.error(f"Query error for {model_name}: {e}")
        return []

async def get_by_id(self, id: strawberry.ID) -> Optional[output_type]:
    try:
        return await sync_to_async(model.objects.get)(id=id)
    except Exception as e:
        logger.error(f"Query error for {model_name}: {e}")
        return None
```

### Configuration System

#### 1. YAML Loading

The configuration system supports multiple formats:

```python
def _load_yaml_config(self, apps_list: List[str]) -> Dict[str, Any]:
    for app_name in apps_list:
        app_config_dir = Path(__file__).parent.parent.parent / "core" / app_name / "gql_config"
        
        # Load defaults first
        defaults = self._load_defaults(app_config_dir)
        
        # Try single models.yml file first
        single_config_path = app_config_dir / "models.yml"
        if single_config_path.exists():
            with open(single_config_path, "r") as file:
                models_config = yaml.safe_load(file)
                if 'models' in models_config:
                    for model_name, model_config in models_config['models'].items():
                        merged_config = self._merge_with_defaults(defaults, model_config)
                        all_configs[model_name] = merged_config
        else:
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
```

#### 2. Default Merging

Deep merging of default and model-specific configurations:

```python
def _merge_with_defaults(self, defaults: dict, model_config: dict) -> dict:
    merged = defaults.copy()
    
    def deep_merge(d1, d2):
        for key, value in d2.items():
            if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
                deep_merge(d1[key], value)
            else:
                d1[key] = value
    
    deep_merge(merged, model_config)
    return merged
```

### Error Handling

#### 1. Comprehensive Error Handling

All operations include proper error handling:

```python
try:
    # Database operation
    obj = await sync_to_async(model.objects.create)(**model_data)
    return await generator._convert_to_graphql_type(obj, output_type)
except Exception as e:
    logger.error(f"Create error for {model_name}: {e}")
    raise Exception(f"Failed to create {model_name}: {str(e)}")
```

#### 2. Logging

Detailed logging for debugging and monitoring:

```python
import logging
logger = logging.getLogger(__name__)

# Usage throughout the code
logger.info(f"Found model: {model.__name__} in app: {app_name}")
logger.warning(f"No gql_config folder found for app: {app_name}")
logger.error(f"Error loading YAML config for app {app_name}: {e}")
```

### Performance Considerations

#### 1. Lazy Loading

Django components are loaded only when needed:

```python
def get_django_components():
    from django.apps import apps
    from django.db import models
    return apps, models
```

#### 2. Type Caching

Generated types are cached to avoid regeneration:

```python
if input_name in self.generated_types:
    return self.generated_types[input_name]

# ... generate type ...

self.generated_types[input_name] = strawberry_input
```

#### 3. Async Operations

All database operations use `sync_to_async` for proper async handling:

```python
# Query operations
queryset = await sync_to_async(list)(queryset)

# Create operations
obj = await sync_to_async(model.objects.create)(**model_data)

# Update operations
await sync_to_async(obj.save)()

# Delete operations
await sync_to_async(obj.delete)()
```

## Extension Points

### 1. Custom Field Types

You can extend the field type mapping:

```python
def get_strawberry_field_type(self, field) -> Any:
    # Add custom field type handling
    if field.get_internal_type() == "CustomField":
        return CustomGraphQLType
    
    # ... existing mapping ...
```

### 2. Custom Relationship Handling

Extend relationship resolution:

```python
async def _convert_to_graphql_type(self, instance, output_type):
    # Add custom relationship handling
    if rel_name == "custom_relationship":
        # Custom logic here
        pass
    
    # ... existing relationship handling ...
```

### 3. Custom Validation

Add validation logic to mutations:

```python
def make_create_func(model, model_name, input_type, output_type, generator):
    async def create(self, input: input_type) -> output_type:
        # Add custom validation
        if not self._validate_input(input):
            raise ValidationError("Invalid input")
        
        # ... existing create logic ...
```

### 4. Custom Error Handling

Extend error handling for specific cases:

```python
try:
    # Operation
    pass
except SpecificException as e:
    # Custom handling
    logger.error(f"Specific error: {e}")
    raise CustomGraphQLError("Custom error message")
except Exception as e:
    # General handling
    logger.error(f"General error: {e}")
    raise Exception(f"Operation failed: {str(e)}")
```

## Testing

### 1. Unit Tests

Test individual components:

```python
def test_enum_generation():
    generator = StrawberryCRUDGenerator()
    field = Person._meta.get_field("gender")
    enum_type = generator.generate_enum_from_choices(field)
    assert enum_type is not None
    assert hasattr(enum_type, "male")
    assert hasattr(enum_type, "female")

def test_type_generation():
    generator = StrawberryCRUDGenerator()
    output_type = generator.generate_output_type(Person)
    assert output_type is not None
    assert "name" in output_type.__annotations__
    assert "gender" in output_type.__annotations__
```

### 2. Integration Tests

Test complete workflows:

```python
def test_complete_schema_generation():
    generator = StrawberryCRUDGenerator(["family"])
    schema = generator.generate_complete_schema(["family"])
    assert schema is not None
    assert schema.query is not None
    assert schema.mutation is not None
```

### 3. End-to-End Tests

Test actual GraphQL operations:

```python
def test_create_mutation():
    query = """
    mutation {
        createPerson(input: { name: "John", gender: male }) {
            id
            name
            gender
        }
    }
    """
    result = schema.execute(query)
    assert result.errors is None
    assert result.data["createPerson"]["name"] == "John"
    assert result.data["createPerson"]["gender"] == "male"
```

## Deployment Considerations

### 1. Production Settings

Ensure proper configuration for production:

```python
# settings/production.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'graphql_generator.log',
        },
    },
    'loggers': {
        'core.graphql_generator': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 2. Caching

Implement caching for better performance:

```python
# Add to your Django settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 3. Monitoring

Add monitoring for the generator:

```python
# Add to your monitoring system
def monitor_generator_performance():
    # Track schema generation time
    # Monitor mutation execution time
    # Track error rates
    pass
```

## Conclusion

The GraphQL Generator provides a powerful, flexible solution for automatically generating GraphQL APIs from Django models. Its modular architecture, comprehensive configuration system, and robust error handling make it suitable for both simple and complex applications.

The implementation follows Django and GraphQL best practices, ensuring compatibility and maintainability. The extensive configuration options and extension points allow for customization while maintaining the core functionality.

For more information, see the main README.md file and the examples directory.
