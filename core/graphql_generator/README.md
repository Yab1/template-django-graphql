# GraphQL Generator for Strawberry Django

A powerful, dynamic GraphQL CRUD automation framework that generates complete GraphQL APIs from Django models using Strawberry Django. This framework eliminates the need for manual GraphQL type definitions, mutations, and queries by automatically generating them based on YAML configuration.

## 🚀 Features

- **Dynamic Schema Generation**: Automatically generates GraphQL types, queries, and mutations from Django models
- **Nested Relationship Support**: Full support for ForeignKey, OneToOne, and ManyToMany relationships with nested creation
- **YAML Configuration**: Flexible, app-based configuration system with defaults and overrides
- **Circular Reference Detection**: Intelligent detection and prevention of infinite nesting in relationships
- **Optional Field Control**: Fine-grained control over which fields are optional vs required
- **Enum Support**: Automatic generation of GraphQL enums from Django TextChoices
- **Audit Fields**: Built-in support for created_at, updated_at, created_by, updated_by fields
- **Relationship Flexibility**: Support for both ID references and inline nested object creation
- **Performance Optimized**: Smart circular reference detection without runtime performance impact

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Advanced Features](#advanced-features)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## 🛠 Installation

### Prerequisites

- Python 3.8+
- Django 3.2+
- Strawberry Django
- PyYAML

### Install Dependencies

```bash
pip install strawberry-django pyyaml
```

### Add to Django Settings

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'strawberry_django',
    'core.graphql_generator',  # Add this
    # ... your other apps
]
```

## 🚀 Quick Start

### 1. Create Your Django Models

```python
# models.py
from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    founded_date = models.DateField()
    is_public = models.BooleanField(default=False)

class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
    ], default='pending')
    
    # Relationships
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="projects")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="projects", null=True, blank=True)
```

### 2. Create YAML Configuration

Create a `gql_config` directory in your app:

```
your_app/
├── models.py
├── gql_config/
│   ├── defaults.yml
│   └── models.yml
```

**defaults.yml** (optional):
```yaml
defaults:
  fields:
    include: "__all__"
    exclude: []
    read_only: ["id", "created_at", "updated_at"]
  relationships:
    max_depth: 2
    nested_creation: false
    nested_updates: false
```

**models.yml**:
```yaml
Company:
  api_name: "company"
  api_description: "Company management"
  
  fields:
    include: ["id", "name", "description", "website", "founded_date", "is_public", "created_at", "updated_at"]
    exclude: []
    read_only: ["id", "created_at", "updated_at"]
  
  relationships:
    projects:
      include: true
      nested_creation: false
      nested_updates: false
      max_depth: 1

Project:
  api_name: "project"
  api_description: "Project management"
  
  fields:
    include: ["id", "name", "description", "start_date", "end_date", "budget", "status", "created_at", "updated_at"]
    exclude: []
    read_only: ["id", "created_at", "updated_at"]
  
  relationships:
    company:
      include: true
      nested_creation:
        enabled: true
        fields:
          include: ["id", "name", "description", "website", "founded_date", "is_public"]
          exclude: []
          read_only: []
        pk: ["id"]  # If id is provided, fetch existing company instead of creating
      nested_updates: false
      max_depth: 1
    department:
      include: true
      nested_creation: false
      nested_updates: false
      max_depth: 1
```

### 3. Generate GraphQL Schema

```python
# schema.py
import strawberry
from core.graphql_generator.strawberry_generator import StrawberryCRUDGenerator

# Initialize the generator
generator = StrawberryCRUDGenerator(['your_app'])

# Generate the complete schema
schema = generator.generate_complete_schema(['your_app'])

# Use in your GraphQL endpoint
```

### 4. Use in Your GraphQL Endpoint

```python
# urls.py
from django.urls import path
from strawberry.django.views import GraphQLView
from .schema import schema

urlpatterns = [
    path('graphql/', GraphQLView.as_view(schema=schema)),
]
```

## ⚙️ Configuration

### YAML Configuration Structure

The framework supports both single-file and multi-file configuration approaches:

#### Single File Approach (`models.yml`)
```yaml
ModelName:
  api_name: "model_name"
  api_description: "Description of the model"
  
  fields:
    include: ["field1", "field2", "field3"]
    exclude: ["field4"]
    read_only: ["id", "created_at", "updated_at"]
  
  relationships:
    related_field:
      include: true
      nested_creation: true
      nested_updates: true
      max_depth: 2
```

#### Multi-File Approach
```
gql_config/
├── defaults.yml
├── company.yml
├── project.yml
└── employee.yml
```

### Configuration Options

#### Field Configuration
- **`include`**: List of fields to include in GraphQL types (use `"__all__"` for all fields)
- **`exclude`**: List of fields to exclude from GraphQL types
- **`read_only`**: List of fields that are read-only (not included in input types)

#### Relationship Configuration
- **`include`**: Whether to include this relationship in GraphQL types
- **`nested_creation`**: Enable nested object creation in mutations
- **`nested_updates`**: Enable nested object updates in mutations
- **`max_depth`**: Maximum depth for nested relationships (prevents infinite nesting)

#### Nested Creation Options
```yaml
relationships:
  company:
    include: true
    nested_creation:
      enabled: true
      fields:
        include: ["id", "name", "description"]
        exclude: []
        read_only: []
        optional: ["description"]  # Make these fields optional
      pk: ["id"]  # Fields that can be used for lookup
    max_depth: 1
```

## 📖 Usage

### Generated GraphQL Operations

The framework automatically generates:

#### Queries
- `allCompanies` - List all companies
- `company(id: ID!)` - Get a single company
- `allProjects` - List all projects
- `project(id: ID!)` - Get a single project

#### Mutations
- `createCompany(input: CompanyInput!)` - Create a new company
- `updateCompany(input: CompanyUpdateInput!)` - Update an existing company
- `deleteCompany(id: ID!)` - Delete a company
- `createProject(input: ProjectInput!)` - Create a new project
- `updateProject(input: ProjectUpdateInput!)` - Update an existing project
- `deleteProject(id: ID!)` - Delete a project

### Example GraphQL Queries

#### Create a Company
```graphql
mutation CreateCompany {
  createCompany(input: {
    name: "Acme Corp"
    description: "A great company"
    website: "https://acme.com"
    foundedDate: "2020-01-01"
    isPublic: true
  }) {
    id
    name
    description
    website
    foundedDate
    isPublic
    createdAt
    updatedAt
  }
}
```

#### Create a Project with Nested Company
```graphql
mutation CreateProject {
  createProject(input: {
    name: "New Project"
    description: "Project description"
    startDate: "2025-01-01"
    endDate: "2025-12-31"
    budget: 100000
    status: active
    company: {
      name: "New Company"
      description: "Company description"
      website: "https://newcompany.com"
      foundedDate: "2020-01-01"
      isPublic: true
    }
  }) {
    id
    name
    description
    startDate
    endDate
    budget
    status
    company {
      id
      name
      description
      website
      foundedDate
      isPublic
    }
  }
}
```

#### Query with Relationships
```graphql
query GetProjects {
  allProjects {
    id
    name
    description
    startDate
    endDate
    budget
    status
    company {
      id
      name
      description
      website
    }
    department {
      id
      name
      description
    }
  }
}
```

## 🔧 Advanced Features

### Circular Reference Detection

The framework automatically detects and prevents circular references in relationships:

```python
# Example: Company -> Department -> Company
# The framework will skip one direction to prevent infinite nesting
```

### Optional Field Control

Control which fields are optional in nested inputs:

```yaml
relationships:
  company:
    nested_creation:
      fields:
        include: ["id", "name", "description", "website"]
        optional: ["description", "website"]  # These become optional
```

### Enum Support

Django TextChoices are automatically converted to GraphQL enums:

```python
# Django model
class Project(models.Model):
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
    ])

# Generated GraphQL enum
enum ProjectStatusEnum {
  active
  inactive
  pending
}
```

### Audit Fields

Built-in support for audit fields:

```python
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
```

## 📚 API Reference

### StrawberryCRUDGenerator

#### Constructor
```python
StrawberryCRUDGenerator(apps_list: List[str] = None)
```

**Parameters:**
- `apps_list`: List of Django app names to include in GraphQL generation

#### Methods

##### `generate_complete_schema(models_list: List[str]) -> strawberry.Schema`
Generates a complete GraphQL schema with queries and mutations.

**Parameters:**
- `models_list`: List of model names to include

**Returns:**
- `strawberry.Schema`: Complete GraphQL schema

##### `generate_output_type(model) -> Type`
Generates a Strawberry output type for a Django model.

##### `generate_input_type(model) -> Type`
Generates a Strawberry input type for a Django model.

##### `generate_nested_input_type(model, current_depth: int, max_depth: int, config_override: dict = None) -> Type`
Generates a nested input type for relationship handling.

### Configuration Methods

#### `_load_yaml_config(apps_list: List[str]) -> Dict[str, Any]`
Loads YAML configuration from app directories.

#### `_merge_with_defaults(defaults: dict, model_config: dict) -> dict`
Merges model configuration with defaults.

## 🎯 Examples

### Complete Example: Blog System

#### Models
```python
# models.py
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="posts")
    categories = models.ManyToManyField(Category, related_name="posts", blank=True)
```

#### Configuration
```yaml
# gql_config/models.yml
Author:
  api_name: "author"
  api_description: "Blog authors"
  
  fields:
    include: ["id", "name", "email", "bio", "created_at", "updated_at"]
    read_only: ["id", "created_at", "updated_at"]

Post:
  api_name: "post"
  api_description: "Blog posts"
  
  fields:
    include: ["id", "title", "content", "published", "created_at", "updated_at"]
    read_only: ["id", "created_at", "updated_at"]
  
  relationships:
    author:
      include: true
      nested_creation:
        enabled: true
        fields:
          include: ["id", "name", "email", "bio"]
          optional: ["bio"]
        pk: ["id"]
      max_depth: 1
    categories:
      include: true
      nested_creation: true
      max_depth: 1
```

#### Generated GraphQL Operations

**Queries:**
```graphql
query GetAllPosts {
  allPosts {
    id
    title
    content
    published
    createdAt
    updatedAt
    author {
      id
      name
      email
      bio
    }
    categories {
      id
      name
      description
    }
  }
}
```

**Mutations:**
```graphql
mutation CreatePost {
  createPost(input: {
    title: "My First Post"
    content: "This is the content of my first post"
    published: true
    author: {
      name: "John Doe"
      email: "john@example.com"
      bio: "A passionate writer"
    }
    categories: [
      {
        name: "Technology"
        description: "Tech-related posts"
      }
    ]
  }) {
    id
    title
    content
    published
    author {
      id
      name
      email
    }
    categories {
      id
      name
    }
  }
}
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Circular Reference Errors
**Problem:** Infinite nesting in relationships
**Solution:** The framework automatically detects and prevents circular references. Check the logs for skipped relationships.

#### 2. Required Field Errors
**Problem:** Fields marked as required in GraphQL but optional in Django
**Solution:** Use the `optional` configuration in nested creation:

```yaml
nested_creation:
  fields:
    optional: ["field_name"]
```

#### 3. Type Definition Errors
**Problem:** "Type defined multiple times" errors
**Solution:** Ensure unique type names in your configuration. The framework handles this automatically.

#### 4. Migration Issues
**Problem:** Database constraint violations
**Solution:** Make sure to run migrations after changing model fields:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Debug Mode

Enable debug logging to see what's happening:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Tips

1. **Limit Relationship Depth**: Use `max_depth` to prevent deep nesting
2. **Selective Field Inclusion**: Only include necessary fields in your configuration
3. **Use ID References**: For existing objects, use ID references instead of nested creation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the examples

---

**Happy GraphQL-ing! 🚀**

