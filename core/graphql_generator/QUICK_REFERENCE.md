# GraphQL Generator - Quick Reference

A quick reference guide for the GraphQL Generator.

## Installation

```python
# config/django/base.py
LOCAL_APPS = [
    # ... other apps
    "core.graphql_generator.apps.GraphQLGeneratorConfig",
]

# config/schema.py
from core.graphql_generator.strawberry_generator import StrawberryCRUDGenerator

framework = StrawberryCRUDGenerator()
graphql_schema = framework.generate_complete_schema(["your_app"])

Query = merge_types("Query", (YourQuery, graphql_schema.query))
Mutation = merge_types("Mutation", (YourMutation, graphql_schema.mutation))
```

## Configuration Structure

```
core/your_app/gql_config/
├── defaults.yml          # Default configuration
├── models.yml            # Single file for all models
├── model1.yml            # Individual model files
└── model2.yml
```

## YAML Configuration

### Basic Model Configuration

```yaml
# models.yml
models:
  YourModel:
    api_name: "your_model"
    api_description: "Your model description"
    
    fields:
      include: ["id", "name", "email", "created_at", "updated_at"]
      exclude: []
      read_only: ["id", "created_at", "updated_at"]
      write_only: []
    
    relationships:
      related_field:
        include: true
        nested_creation: true
        nested_updates: true
        max_depth: 2
```

### Individual Model File

```yaml
# your_model.yml
model: YourModel

api_name: "your_model"
api_description: "Your model description"

fields:
  include: ["id", "name", "email"]
  exclude: []

relationships:
  related_field:
    include: true
    max_depth: 2
```

### Defaults File

```yaml
# defaults.yml
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

## Generated GraphQL API

### Queries

```graphql
# Get all objects
query GetYourModelList {
  getYourModelList(limit: 10) {
    id
    name
    email
    relatedField
  }
}

# Get object by ID
query GetYourModelById {
  getYourModelById(id: "object-id") {
    id
    name
    email
  }
}
```

### Mutations

```graphql
# Create object
mutation CreateYourModel {
  createYourModel(input: {
    name: "John Doe"
    email: "john@example.com"
    status: active
  }) {
    id
    name
    email
    status
  }
}

# Update object
mutation UpdateYourModel {
  updateYourModel(input: {
    id: "object-id"
    name: "Jane Doe"
    email: "jane@example.com"
  }) {
    id
    name
    email
  }
}

# Delete object
mutation DeleteYourModel {
  deleteYourModel(id: "object-id")
}
```

## Django Field Types → GraphQL Types

| Django Field | GraphQL Type | Notes |
|--------------|--------------|-------|
| `CharField` | `String!` | Required string |
| `TextField` | `String!` | Required string |
| `EmailField` | `String!` | Required string |
| `URLField` | `String!` | Required string |
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

## Enum Usage

### Django Model

```python
class StatusChoices(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    PENDING = "pending", "Pending"

class YourModel(models.Model):
    status = models.CharField(max_length=20, choices=StatusChoices.choices)
```

### GraphQL Usage

```graphql
# Input (use lowercase choice values)
mutation {
  createYourModel(input: { 
    name: "Test", 
    status: active 
  }) {
    id
    status
  }
}

# Output (returns choice values)
{
  "data": {
    "createYourModel": {
      "id": "123",
      "status": "active"
    }
  }
}
```

## Relationship Types

### ForeignKey

```python
class Author(models.Model):
    name = models.CharField(max_length=255)

class Post(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
```

**Generated GraphQL:**
```graphql
type PostType {
  id: ID!
  title: String!
  author: ID!  # Author ID
}

type AuthorType {
  id: ID!
  name: String!
  posts: [ID!]!  # List of Post IDs (reverse relationship)
}
```

### ManyToMany

```python
class Tag(models.Model):
    name = models.CharField(max_length=100)

class Post(models.Model):
    title = models.CharField(max_length=255)
    tags = models.ManyToManyField(Tag)
```

**Generated GraphQL:**
```graphql
type PostType {
  id: ID!
  title: String!
  tags: [ID!]!  # List of Tag IDs
}

type TagType {
  id: ID!
  name: String!
  posts: [ID!]!  # List of Post IDs (reverse relationship)
}
```

## Common Configuration Options

### Field Configuration

```yaml
fields:
  include: ["id", "name", "email"]     # Only include these fields
  exclude: ["password", "secret"]      # Exclude these fields
  read_only: ["id", "created_at"]      # Read-only fields
  write_only: ["password"]             # Write-only fields
```

### Relationship Configuration

```yaml
relationships:
  related_field:
    include: true                      # Include this relationship
    nested_creation: true             # Allow nested creation
    nested_updates: true              # Allow nested updates
    max_depth: 2                      # Maximum relationship depth
```

### Security Configuration

```yaml
security:
  login_required: true                # Require authentication
  permissions:                        # Required permissions
    - "app.view_model"
    - "app.add_model"
  sensitive_fields: ["password"]      # Sensitive fields to mask
```

### Cache Configuration

```yaml
cache:
  enabled: true                       # Enable caching
  ttl: 300                           # Time to live in seconds
  key_prefix: "gql_"                 # Cache key prefix
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "No gql_config folder found" | Create `gql_config` directory in your app |
| "Type must define one or more fields" | Check `fields.include` is not empty |
| "Enum cannot represent value" | Use lowercase choice values in GraphQL |
| "Field not found in model" | Check relationship name matches Django field |
| "Cannot access free variable" | Update to latest version |

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('core.graphql_generator')
```

### Performance Tips

1. **Use specific field lists** instead of relying on defaults
2. **Limit relationship depth** to avoid N+1 queries
3. **Enable caching** for frequently accessed data
4. **Only include necessary fields** in your queries

## Examples

### Complete Blog System

```python
# models.py
class Author(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()

class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="posts")
    is_published = models.BooleanField(default=False)
```

```yaml
# gql_config/models.yml
models:
  Author:
    fields:
      include: ["id", "name", "email"]
    relationships:
      posts:
        include: true
        max_depth: 1

  Post:
    fields:
      include: ["id", "title", "content", "is_published"]
    relationships:
      author:
        include: true
        max_depth: 1
```

```graphql
# Usage
mutation CreatePost {
  createPost(input: {
    title: "My First Post"
    content: "This is the content..."
    author: "author-id"
    isPublished: true
  }) {
    id
    title
    content
    isPublished
    author
  }
}

query GetPosts {
  getPostList {
    id
    title
    content
    isPublished
    author
  }
}
```

## API Reference

### StrawberryCRUDGenerator

```python
# Initialize
generator = StrawberryCRUDGenerator(["app1", "app2"])

# Generate complete schema
schema = generator.generate_complete_schema(["app1", "app2"])

# Generate individual types
input_type = generator.generate_input_type(YourModel)
output_type = generator.generate_output_type(YourModel)
enum_type = generator.generate_enum_from_choices(field)
```

### Generated Operations

**Queries:**
- `get{ModelName}List(limit: Int = 10): [{ModelName}Type!]!`
- `get{ModelName}ById(id: ID!): {ModelName}Type`

**Mutations:**
- `create{ModelName}(input: {ModelName}Input!): {ModelName}Type!`
- `update{ModelName}(input: {ModelName}UpdateInput!): {ModelName}Type!`
- `delete{ModelName}(id: ID!): Boolean!`

**Types:**
- `{ModelName}Type` - Output type
- `{ModelName}Input` - Input type for creation
- `{ModelName}UpdateInput` - Input type for updates
- `{ModelName}{Field}Enum` - Enum types for choice fields

---

**Need more help?** Check the full documentation in README.md and IMPLEMENTATION.md
