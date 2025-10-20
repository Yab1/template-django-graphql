# GraphQL Generator for Strawberry Django

A dynamic GraphQL CRUD generator for Strawberry Django that automatically generates GraphQL types, queries, and mutations from Django models and YAML configuration.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Advanced Features](#advanced-features)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

The GraphQL Generator is a Django app that automatically generates complete GraphQL APIs from your Django models. It eliminates the need to manually write GraphQL types, queries, and mutations, saving significant development time while maintaining full control over the generated API.

### Key Benefits

- **🚀 Zero Boilerplate**: Generate complete CRUD APIs from Django models
- **⚡ Dynamic Generation**: No hardcoded types - everything generated at runtime
- **🔧 Highly Configurable**: YAML-based configuration system
- **🎯 Type Safe**: Full TypeScript/GraphQL type safety
- **🔗 Relationship Support**: Automatic handling of ForeignKey, OneToOne, and ManyToMany relationships
- **📊 Enum Support**: Automatic GraphQL enum generation from Django choices
- **🛡️ Security Ready**: Built-in support for permissions and authentication
- **📱 Microservices Friendly**: Perfect for microservices architecture

## Features

### Core Features

- **Dynamic Type Generation**: Automatically generates GraphQL types from Django models
- **CRUD Operations**: Complete Create, Read, Update, Delete operations
- **Relationship Handling**: Automatic handling of all Django relationship types
- **Enum Generation**: Converts Django TextChoices to GraphQL enums
- **YAML Configuration**: Flexible, app-based configuration system
- **Async Support**: Full async/await support for all operations
- **Error Handling**: Comprehensive error handling and logging

### Advanced Features

- **Nested Configuration**: Support for both single and multiple YAML files per app
- **Default Inheritance**: YAML defaults with model-specific overrides
- **Field Filtering**: Include/exclude specific fields per model
- **Relationship Depth Control**: Configurable relationship depth
- **Custom Field Types**: Support for all Django field types
- **Audit Fields**: Automatic handling of created_at, updated_at fields

## Installation

### 1. Add to Django Settings

Add the GraphQL Generator to your `INSTALLED_APPS`:

```python
# config/django/base.py
LOCAL_APPS = [
    "core.common.apps.CommonConfig",
    "core.users.apps.UsersConfig",
    "core.family.apps.FamilyConfig",
    "core.graphql_generator.apps.GraphQLGeneratorConfig",  # Add this
]
```

### 2. Update GraphQL Schema

Update your main GraphQL schema to use the generator:

```python
# config/schema.py
import strawberry
from strawberry.tools import merge_types
from strawberry_django.optimizer import DjangoOptimizerExtension

# Import GraphQL Generator
from core.graphql_generator.strawberry_generator import StrawberryCRUDGenerator

# Initialize the GraphQL Generator
framework = StrawberryCRUDGenerator()

# Generate GraphQL queries and mutations
graphql_schema = framework.generate_complete_schema(["family"])  # Add your apps here

# Merge with existing schema
Query = merge_types("Query", (YourExistingQuery, graphql_schema.query))
Mutation = merge_types("Mutation", (YourExistingMutation, graphql_schema.mutation))

# Create final schema
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[DjangoOptimizerExtension],
    config=StrawberryConfig(auto_camel_case=True),
)
```

## Quick Start

### 1. Create a Django Model

```python
# core/family/models.py
from django.db import models
from core.common.models import BaseModel

class GenderChoices(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"

class Person(BaseModel):
    name = models.CharField(max_length=255)
    gender = models.CharField(max_length=255, choices=GenderChoices.choices)
    age = models.IntegerField()
    
    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "People"
```

### 2. Create YAML Configuration

Create the configuration directory and files:

```bash
mkdir -p core/family/gql_config
```

Create `core/family/gql_config/models.yml`:

```yaml
models:
  Person:
    api_name: "person"
    api_description: "Person management"
    
    fields:
      include: ["id", "name", "gender", "age", "created_at", "updated_at"]
      exclude: []
    
    relationships:
      # Add relationship configurations here
```

### 3. Generate GraphQL API

The generator will automatically create:

**Queries:**
- `getPersonList(limit: Int = 10): [PersonType!]!`
- `getPersonById(id: ID!): PersonType`

**Mutations:**
- `createPerson(input: PersonInput!): PersonType!`
- `updatePerson(input: PersonUpdateInput!): PersonType!`
- `deletePerson(id: ID!): Boolean!`

**Types:**
- `PersonType` - Output type with all fields
- `PersonInput` - Input type for creation
- `PersonUpdateInput` - Input type for updates
- `PersonGenderEnum` - Enum for gender choices

### 4. Use the API

```graphql
# Create a person
mutation CreatePerson {
  createPerson(input: { 
    name: "John Doe", 
    gender: male, 
    age: 30 
  }) {
    id
    name
    gender
    age
    createdAt
  }
}

# Get all persons
query GetPersons {
  getPersonList {
    id
    name
    gender
    age
  }
}

# Update a person
mutation UpdatePerson {
  updatePerson(input: { 
    id: "person-id", 
    name: "Jane Doe", 
    gender: female 
  }) {
    id
    name
    gender
  }
}
```

## Configuration

### Directory Structure

```
core/
├── your_app/
│   ├── models.py
│   └── gql_config/
│       ├── defaults.yml          # Default configuration
│       ├── models.yml            # Single file for all models
│       ├── model1.yml            # Individual model files
│       ├── model2.yml
│       └── ...
```

### YAML Configuration Format

#### Single Models File (`models.yml`)

```yaml
models:
  Person:
    api_name: "person"
    api_description: "Person management"
    
    fields:
      include: ["id", "name", "gender", "age"]
      exclude: []
      read_only: ["id", "created_at", "updated_at"]
      write_only: []
    
    relationships:
      children:
        include: true
        nested_creation: true
        nested_updates: true
        max_depth: 2
      parent:
        include: true
        nested_creation: false
        nested_updates: false
        max_depth: 1
    
    security:
      login_required: true
      permissions: ["family.view_person", "family.add_person"]
    
    cache:
      enabled: true
      ttl: 300
    
    business_rules:
      name_required: "Name must be provided"
      unique_name: "Name must be unique"
```

#### Individual Model Files (`person.yml`)

```yaml
model: Person

api_name: "person"
api_description: "Person management"

fields:
  include: ["id", "name", "gender", "age"]
  exclude: []

relationships:
  children:
    include: true
    nested_creation: true
    max_depth: 2
```

#### Defaults File (`defaults.yml`)

```yaml
defaults:
  fields:
    include: ["id", "name", "created_at", "updated_at"]
    exclude: []
  
  relationships:
    max_depth: 2
    nested_creation: true
    nested_updates: true
  
  security:
    login_required: false
  
  cache:
    enabled: true
    ttl: 300
```

### Configuration Options

#### Field Configuration

```yaml
fields:
  include: ["field1", "field2"]     # Only include these fields
  exclude: ["field3", "field4"]     # Exclude these fields
  read_only: ["id", "created_at"]   # Read-only fields
  write_only: ["password"]          # Write-only fields
```

#### Relationship Configuration

```yaml
relationships:
  related_field:
    include: true                   # Include this relationship
    nested_creation: true          # Allow nested creation
    nested_updates: true           # Allow nested updates
    max_depth: 2                   # Maximum relationship depth
```

#### Security Configuration

```yaml
security:
  login_required: true             # Require authentication
  permissions:                     # Required permissions
    - "app.view_model"
    - "app.add_model"
  sensitive_fields: ["password"]   # Sensitive fields to mask
```

#### Cache Configuration

```yaml
cache:
  enabled: true                    # Enable caching
  ttl: 300                        # Time to live in seconds
  key_prefix: "gql_"              # Cache key prefix
```

## Usage

### Basic Usage

```python
from core.graphql_generator.strawberry_generator import StrawberryCRUDGenerator

# Initialize generator
generator = StrawberryCRUDGenerator()

# Generate schema for specific apps
schema = generator.generate_complete_schema(["family", "users"])

# Use in your GraphQL schema
Query = merge_types("Query", (YourQuery, schema.query))
Mutation = merge_types("Mutation", (YourMutation, schema.mutation))
```

### Advanced Usage

```python
# Initialize with specific apps
generator = StrawberryCRUDGenerator(["family", "users", "products"])

# Generate individual components
input_type = generator.generate_input_type(YourModel)
output_type = generator.generate_output_type(YourModel)
enum_type = generator.generate_enum_from_choices(YourModel._meta.get_field("status"))

# Generate complete schema
schema = generator.generate_complete_schema(["family"])
```

### Custom Field Types

The generator automatically handles all Django field types:

| Django Field | GraphQL Type | Notes |
|--------------|--------------|-------|
| `CharField` | `String!` | Required string |
| `TextField` | `String!` | Required string |
| `IntegerField` | `Int!` | Required integer |
| `FloatField` | `Float!` | Required float |
| `BooleanField` | `Boolean!` | Required boolean |
| `DateTimeField` | `DateTime!` | Required datetime |
| `DateField` | `Date!` | Required date |
| `UUIDField` | `ID!` | Required ID |
| `ForeignKey` | `ID!` | Related object ID |
| `OneToOneField` | `ID!` | Related object ID |
| `ManyToManyField` | `[ID!]!` | List of related object IDs |
| `TextChoices` | `Enum!` | Custom enum type |

### Enum Handling

Django `TextChoices` are automatically converted to GraphQL enums:

```python
class StatusChoices(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    PENDING = "pending", "Pending"

# Becomes GraphQL enum:
enum StatusEnum {
  active
  inactive
  pending
}
```

**Usage in GraphQL:**
```graphql
# Input (use the choice value)
mutation {
  createModel(input: { status: active }) {
    id
    status
  }
}

# Output (returns the choice value)
{
  "data": {
    "createModel": {
      "id": "123",
      "status": "active"
    }
  }
}
```

## API Reference

### StrawberryCRUDGenerator

Main generator class for creating GraphQL schemas.

#### Constructor

```python
StrawberryCRUDGenerator(apps_list: List[str] = None)
```

**Parameters:**
- `apps_list`: List of Django app names to include in the schema

#### Methods

##### `generate_complete_schema(apps_list: List[str]) -> strawberry.Schema`

Generates a complete GraphQL schema with queries and mutations for all models in the specified apps.

**Parameters:**
- `apps_list`: List of Django app names

**Returns:**
- `strawberry.Schema`: Complete GraphQL schema

**Example:**
```python
generator = StrawberryCRUDGenerator()
schema = generator.generate_complete_schema(["family", "users"])
```

##### `generate_input_type(model) -> Type`

Generates a Strawberry input type for a Django model.

**Parameters:**
- `model`: Django model class

**Returns:**
- `Type`: Strawberry input type

**Example:**
```python
input_type = generator.generate_input_type(Person)
```

##### `generate_output_type(model) -> Type`

Generates a Strawberry output type for a Django model.

**Parameters:**
- `model`: Django model class

**Returns:**
- `Type`: Strawberry output type

**Example:**
```python
output_type = generator.generate_output_type(Person)
```

##### `generate_enum_from_choices(field) -> Optional[Type[Enum]]`

Generates a Strawberry enum from a Django field with choices.

**Parameters:**
- `field`: Django model field with choices

**Returns:**
- `Optional[Type[Enum]]`: Strawberry enum type or None

**Example:**
```python
field = Person._meta.get_field("gender")
enum_type = generator.generate_enum_from_choices(field)
```

##### `find_all_models(apps_list: List[str]) -> List`

Finds all Django models in the specified apps that have YAML configuration.

**Parameters:**
- `apps_list`: List of Django app names

**Returns:**
- `List`: List of Django model classes

##### `_load_yaml_config(apps_list: List[str]) -> Dict[str, Any]`

Loads YAML configuration from all specified apps.

**Parameters:**
- `apps_list`: List of Django app names

**Returns:**
- `Dict[str, Any]`: Merged configuration dictionary

## Advanced Features

### Relationship Handling

The generator automatically handles all Django relationship types:

#### ForeignKey Relationships

```python
class Person(BaseModel):
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

class Company(BaseModel):
    name = models.CharField(max_length=255)
```

**Generated GraphQL:**
```graphql
type PersonType {
  id: ID!
  name: String!
  company: ID!  # Company ID
}

type CompanyType {
  id: ID!
  name: String!
  persons: [ID!]!  # List of Person IDs (reverse relationship)
}
```

#### ManyToMany Relationships

```python
class Person(BaseModel):
    name = models.CharField(max_length=255)
    tags = models.ManyToManyField(Tag)

class Tag(BaseModel):
    name = models.CharField(max_length=255)
```

**Generated GraphQL:**
```graphql
type PersonType {
  id: ID!
  name: String!
  tags: [ID!]!  # List of Tag IDs
}

type TagType {
  id: ID!
  name: String!
  persons: [ID!]!  # List of Person IDs (reverse relationship)
}
```

### Nested Configuration

You can use either a single `models.yml` file or individual model files:

#### Single File Approach

```yaml
# core/family/gql_config/models.yml
models:
  Person:
    fields:
      include: ["id", "name", "email"]
  Company:
    fields:
      include: ["id", "name", "address"]
```

#### Multiple Files Approach

```yaml
# core/family/gql_config/person.yml
model: Person
fields:
  include: ["id", "name", "email"]

# core/family/gql_config/company.yml
model: Company
fields:
  include: ["id", "name", "address"]
```

### Default Inheritance

Use `defaults.yml` to define common settings:

```yaml
# core/family/gql_config/defaults.yml
defaults:
  fields:
    include: ["id", "name", "created_at", "updated_at"]
  relationships:
    max_depth: 2
  security:
    login_required: true
```

Individual model files will inherit these defaults and can override them:

```yaml
# core/family/gql_config/person.yml
model: Person
fields:
  include: ["id", "name", "email", "phone"]  # Overrides defaults
  exclude: ["created_at"]  # Excludes created_at from defaults
```

## Examples

### Complete Example

Let's create a complete example with a blog system:

#### 1. Django Models

```python
# core/blog/models.py
from django.db import models
from core.common.models import BaseModel

class CategoryChoices(models.TextChoices):
    TECHNOLOGY = "tech", "Technology"
    LIFESTYLE = "lifestyle", "Lifestyle"
    TRAVEL = "travel", "Travel"

class Author(BaseModel):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    bio = models.TextField(blank=True)

class Category(BaseModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

class Post(BaseModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CategoryChoices.choices)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="posts")
    categories = models.ManyToManyField(Category, related_name="posts")
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
```

#### 2. YAML Configuration

```yaml
# core/blog/gql_config/models.yml
models:
  Author:
    api_name: "author"
    api_description: "Blog author management"
    
    fields:
      include: ["id", "name", "email", "bio", "created_at", "updated_at"]
    
    relationships:
      posts:
        include: true
        max_depth: 1

  Category:
    api_name: "category"
    api_description: "Blog category management"
    
    fields:
      include: ["id", "name", "slug", "description", "created_at", "updated_at"]
    
    relationships:
      posts:
        include: true
        max_depth: 1

  Post:
    api_name: "post"
    api_description: "Blog post management"
    
    fields:
      include: ["id", "title", "slug", "content", "excerpt", "category", "is_published", "published_at", "created_at", "updated_at"]
      exclude: []
    
    relationships:
      author:
        include: true
        max_depth: 1
      categories:
        include: true
        max_depth: 1
```

#### 3. Generated GraphQL API

**Queries:**
```graphql
# Get all authors
query GetAuthors {
  getAuthorList {
    id
    name
    email
    bio
    posts
  }
}

# Get author by ID
query GetAuthor {
  getAuthorById(id: "author-id") {
    id
    name
    email
    bio
  }
}

# Get all posts
query GetPosts {
  getPostList {
    id
    title
    slug
    content
    category
    isPublished
    publishedAt
    author
    categories
  }
}
```

**Mutations:**
```graphql
# Create author
mutation CreateAuthor {
  createAuthor(input: {
    name: "John Doe"
    email: "john@example.com"
    bio: "Software developer and blogger"
  }) {
    id
    name
    email
    bio
  }
}

# Create post
mutation CreatePost {
  createPost(input: {
    title: "My First Post"
    slug: "my-first-post"
    content: "This is the content of my first post..."
    excerpt: "A brief excerpt..."
    category: tech
    author: "author-id"
    isPublished: true
  }) {
    id
    title
    slug
    category
    isPublished
  }
}

# Update post
mutation UpdatePost {
  updatePost(input: {
    id: "post-id"
    title: "Updated Post Title"
    isPublished: false
  }) {
    id
    title
    isPublished
  }
}

# Delete post
mutation DeletePost {
  deletePost(id: "post-id")
}
```

**Types:**
```graphql
type AuthorType {
  id: ID!
  name: String!
  email: String!
  bio: String!
  posts: [ID!]!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type PostType {
  id: ID!
  title: String!
  slug: String!
  content: String!
  excerpt: String!
  category: PostCategoryEnum!
  isPublished: Boolean!
  publishedAt: DateTime
  author: ID!
  categories: [ID!]!
  createdAt: DateTime!
  updatedAt: DateTime!
}

enum PostCategoryEnum {
  tech
  lifestyle
  travel
}

input AuthorInput {
  name: String!
  email: String!
  bio: String!
}

input PostInput {
  title: String!
  slug: String!
  content: String!
  excerpt: String!
  category: PostCategoryEnum!
  author: ID!
  isPublished: Boolean!
  publishedAt: DateTime
}

input PostUpdateInput {
  id: ID!
  title: String
  slug: String
  content: String
  excerpt: String
  category: PostCategoryEnum
  author: ID
  isPublished: Boolean
  publishedAt: DateTime
}
```

## Troubleshooting

### Common Issues

#### 1. "No gql_config folder found for app"

**Problem:** The generator can't find the configuration directory.

**Solution:** Create the `gql_config` directory in your app:
```bash
mkdir -p core/your_app/gql_config
```

#### 2. "Type must define one or more fields"

**Problem:** Generated types have no fields.

**Solution:** Check your YAML configuration and ensure fields are properly included:
```yaml
fields:
  include: ["id", "name", "email"]  # Make sure this is not empty
```

#### 3. "Enum cannot represent value"

**Problem:** Enum values don't match the expected format.

**Solution:** Use the actual choice values (lowercase) in your GraphQL queries:
```graphql
# Correct
mutation { createModel(input: { status: active }) }

# Incorrect
mutation { createModel(input: { status: ACTIVE }) }
```

#### 4. "Field not found in model"

**Problem:** Relationship field not found in the model.

**Solution:** Check that the relationship name matches the Django model's related_name or field name:
```python
# Model definition
class Post(models.Model):
    author = models.ForeignKey(Author, related_name="posts")

# YAML configuration
relationships:
  posts:  # This should match the related_name
    include: true
```

#### 5. "Cannot access free variable in enclosing scope"

**Problem:** Async function scope issues.

**Solution:** This is handled automatically by the generator. If you encounter this, ensure you're using the latest version.

### Debug Mode

Enable debug logging to see what's happening:

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('core.graphql_generator')
```

### Performance Considerations

1. **Large Datasets**: Use pagination for large result sets
2. **Complex Relationships**: Limit relationship depth to avoid N+1 queries
3. **Caching**: Enable caching for frequently accessed data
4. **Field Selection**: Only include necessary fields in your queries

### Best Practices

1. **Use Specific Field Lists**: Always specify `include` fields instead of relying on defaults
2. **Limit Relationship Depth**: Set appropriate `max_depth` values
3. **Use Read-Only Fields**: Mark audit fields as read-only
4. **Validate Input**: Add business rules in your YAML configuration
5. **Test Thoroughly**: Test all generated operations before production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

1. Check the troubleshooting section
2. Review the examples
3. Open an issue on GitHub
4. Contact the development team

---

**Happy coding with GraphQL Generator! 🚀**
