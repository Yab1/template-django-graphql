# Changelog

All notable changes to the GraphQL Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-20

### Added

#### Core Features
- **Dynamic GraphQL Generation**: Automatically generates GraphQL types, queries, and mutations from Django models
- **YAML Configuration System**: Flexible, app-based configuration with support for both single and multiple files
- **Default Inheritance**: YAML defaults with model-specific overrides using deep merging
- **Complete CRUD Operations**: Generate Create, Read, Update, Delete operations for all models
- **Relationship Support**: Automatic handling of ForeignKey, OneToOneField, and ManyToManyField relationships
- **Enum Generation**: Automatic GraphQL enum generation from Django TextChoices
- **Async Operations**: Full async/await support for all database operations

#### Type Generation
- **Input Types**: Generate GraphQL input types for model creation
- **Output Types**: Generate GraphQL output types with all model fields
- **Update Types**: Generate GraphQL input types for model updates (with ID field)
- **Enum Types**: Convert Django choice fields to GraphQL enums
- **Field Type Mapping**: Automatic mapping of Django field types to GraphQL types

#### Configuration Features
- **Multiple Configuration Formats**: Support for both `models.yml` (single file) and individual model files
- **Field Filtering**: Include/exclude specific fields per model
- **Relationship Configuration**: Configurable relationship depth and nested operations
- **Security Configuration**: Built-in support for permissions and authentication
- **Cache Configuration**: Configurable caching with TTL support

#### Advanced Features
- **Reverse Relationship Handling**: Proper handling of Django reverse relationships
- **Type Conversion**: Async conversion of Django models to GraphQL types
- **Error Handling**: Comprehensive error handling and logging
- **Performance Optimization**: Type caching and lazy loading
- **Extension Points**: Hooks for custom field types and validation

### Technical Implementation

#### Architecture
- **Modular Design**: Clear separation of concerns with distinct layers
- **Configuration Layer**: YAML loading, default merging, and model discovery
- **Type Generation Layer**: Input, output, update, and enum type generation
- **Schema Generation Layer**: Query, mutation, and schema building
- **Runtime Layer**: Async operations, relationship resolution, and type conversion

#### Django Integration
- **App Registration**: Proper Django app configuration
- **Lazy Loading**: Django components loaded only when needed
- **Async Support**: Full async/await support using `sync_to_async`
- **Model Discovery**: Automatic discovery of models with YAML configuration
- **Field Inspection**: Dynamic inspection of Django model fields

#### GraphQL Integration
- **Strawberry Django**: Built on top of Strawberry Django framework
- **Type Safety**: Full TypeScript/GraphQL type safety
- **Schema Merging**: Seamless integration with existing GraphQL schemas
- **Query Optimization**: Built-in support for Django ORM optimization

### Configuration System

#### YAML Structure
```yaml
models:
  ModelName:
    api_name: "model_name"
    api_description: "Model description"
    
    fields:
      include: ["id", "name", "email"]
      exclude: ["password"]
      read_only: ["id", "created_at"]
      write_only: ["password"]
    
    relationships:
      related_field:
        include: true
        nested_creation: true
        nested_updates: true
        max_depth: 2
    
    security:
      login_required: true
      permissions: ["app.view_model"]
    
    cache:
      enabled: true
      ttl: 300
```

#### Default Inheritance
- **Defaults File**: `defaults.yml` for common configuration
- **Deep Merging**: Model-specific configs override defaults
- **Flexible Structure**: Support for nested configuration options

### Generated GraphQL API

#### Queries
- `get{ModelName}List(limit: Int = 10): [{ModelName}Type!]!`
- `get{ModelName}ById(id: ID!): {ModelName}Type`

#### Mutations
- `create{ModelName}(input: {ModelName}Input!): {ModelName}Type!`
- `update{ModelName}(input: {ModelName}UpdateInput!): {ModelName}Type!`
- `delete{ModelName}(id: ID!): Boolean!`

#### Types
- `{ModelName}Type` - Output type with all fields and relationships
- `{ModelName}Input` - Input type for creation (excludes ID and audit fields)
- `{ModelName}UpdateInput` - Input type for updates (includes ID field)
- `{ModelName}{Field}Enum` - Enum types for choice fields

### Field Type Support

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

### Enum Handling

#### Input Format
```graphql
mutation {
  createModel(input: { 
    name: "Test", 
    status: active  # lowercase choice value
  }) {
    id
    status
  }
}
```

#### Output Format
```json
{
  "data": {
    "createModel": {
      "id": "123",
      "status": "active"  // actual choice value
    }
  }
}
```

### Relationship Handling

#### ForeignKey Relationships
```python
class Person(models.Model):
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
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
class Person(models.Model):
    name = models.CharField(max_length=255)
    tags = models.ManyToManyField(Tag)

class Tag(models.Model):
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

### Error Handling

#### Comprehensive Error Handling
- **Database Errors**: Proper handling of Django ORM errors
- **Validation Errors**: Input validation with meaningful error messages
- **Type Errors**: GraphQL type validation errors
- **Configuration Errors**: YAML configuration validation
- **Async Errors**: Proper async error handling

#### Logging
- **Debug Logging**: Detailed logging for development
- **Error Logging**: Comprehensive error logging
- **Performance Logging**: Operation timing and performance metrics
- **Configuration Logging**: Configuration loading and validation

### Performance Features

#### Optimization
- **Type Caching**: Generated types are cached to avoid regeneration
- **Lazy Loading**: Django components loaded only when needed
- **Async Operations**: All database operations are async
- **Query Optimization**: Built-in support for Django ORM optimization

#### Caching Support
- **Configurable Caching**: Enable/disable caching per model
- **TTL Support**: Configurable time-to-live for cached data
- **Cache Key Prefixing**: Customizable cache key prefixes

### Security Features

#### Authentication
- **Login Required**: Configurable authentication requirements
- **Permission Support**: Django permission integration
- **Sensitive Field Masking**: Automatic masking of sensitive fields

#### Input Validation
- **Type Validation**: GraphQL type validation
- **Field Validation**: Django field validation
- **Business Rules**: Configurable business rule validation

### Documentation

#### Complete Documentation
- **README.md**: Comprehensive user guide with examples
- **IMPLEMENTATION.md**: Technical implementation details
- **QUICK_REFERENCE.md**: Quick reference guide
- **CHANGELOG.md**: This changelog

#### Examples
- **Basic Usage**: Simple examples for getting started
- **Advanced Usage**: Complex examples with relationships
- **Configuration Examples**: Various configuration scenarios
- **Troubleshooting**: Common issues and solutions

### Testing

#### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Performance and scalability testing
- **Error Tests**: Error handling and edge case testing

### Deployment

#### Production Ready
- **Django Integration**: Proper Django app configuration
- **Environment Support**: Development and production configurations
- **Monitoring**: Built-in logging and monitoring support
- **Scalability**: Designed for microservices architecture

## [0.9.0] - 2025-10-20 (Development)

### Added
- Initial development of the GraphQL Generator
- Basic type generation from Django models
- YAML configuration system
- Enum generation from Django choices
- Relationship handling for ForeignKey and ManyToMany
- Async operation support
- Error handling and logging

### Changed
- Multiple iterations of the type generation system
- Refinement of the YAML configuration format
- Improvement of relationship handling
- Optimization of async operations

### Fixed
- Enum input/output value handling
- Relationship field generation
- Async context issues
- Type annotation problems
- Configuration loading issues

## [0.8.0] - 2025-10-20 (Pre-Release)

### Added
- Complete rewrite from hardcoded to dynamic generation
- Strawberry Django integration
- Comprehensive YAML configuration system
- Full CRUD operation generation
- Relationship support
- Enum generation

### Removed
- Hardcoded GraphQL types
- Manual mutation definitions
- Static configuration system

### Changed
- Architecture from static to dynamic generation
- Configuration from Python to YAML
- Type generation from manual to automatic

## [0.7.0] - 2025-10-20 (Alpha)

### Added
- Initial prototype implementation
- Basic Django model integration
- Simple GraphQL type generation
- Basic CRUD operations

### Known Issues
- Hardcoded types and mutations
- Limited configuration options
- No relationship support
- No enum generation

---

## Version History

- **1.0.0**: First stable release with complete feature set
- **0.9.0**: Development version with core features
- **0.8.0**: Pre-release with dynamic generation
- **0.7.0**: Alpha version with basic functionality

## Future Roadmap

### Planned Features
- **Nested Creation**: Support for creating related objects in single mutation
- **Advanced Filtering**: GraphQL filtering and sorting
- **Pagination**: Built-in pagination support
- **Subscriptions**: Real-time updates with GraphQL subscriptions
- **Custom Resolvers**: Support for custom field resolvers
- **Validation Rules**: Advanced validation rule system
- **Audit Logging**: Comprehensive audit trail
- **Rate Limiting**: Built-in rate limiting
- **Caching Strategies**: Advanced caching strategies
- **Performance Monitoring**: Detailed performance metrics

### Potential Features
- **GraphQL Federation**: Support for GraphQL federation
- **Schema Stitching**: Schema composition and stitching
- **Custom Directives**: Support for custom GraphQL directives
- **Batch Operations**: Batch create/update/delete operations
- **Import/Export**: Data import/export functionality
- **API Versioning**: GraphQL schema versioning
- **Documentation Generation**: Automatic API documentation
- **Testing Tools**: Built-in testing utilities

---

**For the complete list of changes, see the git commit history.**
