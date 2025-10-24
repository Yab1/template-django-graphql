"""
Comprehensive Test Models for GraphQL Generator
Covers all Django field types and relationships for testing
"""

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.common.models import BaseModel


# Choice Enums
class StatusChoices(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    PENDING = "pending", "Pending"
    ARCHIVED = "archived", "Archived"


class PriorityChoices(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class ColorChoices(models.TextChoices):
    RED = "red", "Red"
    GREEN = "green", "Green"
    BLUE = "blue", "Blue"
    YELLOW = "yellow", "Yellow"
    BLACK = "black", "Black"
    WHITE = "white", "White"


# Basic Models for Relationships
class Category(BaseModel):
    """Simple model for ForeignKey testing"""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Tag(BaseModel):
    """Simple model for ManyToMany testing"""

    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=20, choices=ColorChoices.choices, default=ColorChoices.BLUE)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.name


class Author(BaseModel):
    """Author model for OneToOne testing"""

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"

    def __str__(self):
        return self.name


# Comprehensive Test Model
class TestModel(BaseModel):
    """
    Comprehensive test model covering all Django field types
    """

    # String Fields
    char_field = models.CharField(max_length=255, help_text="CharField example")
    text_field = models.TextField(help_text="TextField example", blank=True)
    email_field = models.EmailField(help_text="EmailField example", blank=True)
    url_field = models.URLField(help_text="URLField example", blank=True)
    slug_field = models.SlugField(help_text="SlugField example", blank=True)

    # Numeric Fields
    integer_field = models.IntegerField(help_text="IntegerField example", null=True, blank=True)
    big_integer_field = models.BigIntegerField(help_text="BigIntegerField example", null=True, blank=True)
    small_integer_field = models.SmallIntegerField(help_text="SmallIntegerField example", null=True, blank=True)
    positive_integer_field = models.PositiveIntegerField(
        help_text="PositiveIntegerField example",
        null=True,
        blank=True,
    )
    positive_big_integer_field = models.PositiveBigIntegerField(
        help_text="PositiveBigIntegerField example",
        null=True,
        blank=True,
    )
    float_field = models.FloatField(help_text="FloatField example", null=True, blank=True)
    decimal_field = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="DecimalField example",
        null=True,
        blank=True,
    )

    # Boolean Fields
    boolean_field = models.BooleanField(default=False, help_text="BooleanField example")
    null_boolean_field = models.BooleanField(null=True, blank=True, help_text="NullBooleanField example")

    # Date/Time Fields
    date_field = models.DateField(help_text="DateField example", null=True, blank=True)
    time_field = models.TimeField(help_text="TimeField example", null=True, blank=True)
    datetime_field = models.DateTimeField(help_text="DateTimeField example", null=True, blank=True)
    duration_field = models.DurationField(help_text="DurationField example", null=True, blank=True)

    # File Fields
    file_field = models.FileField(upload_to="test_files/", help_text="FileField example", null=True, blank=True)
    image_field = models.ImageField(upload_to="test_images/", help_text="ImageField example", null=True, blank=True)

    # Choice Fields
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        help_text="Status choice field",
    )
    priority = models.CharField(
        max_length=20,
        choices=PriorityChoices.choices,
        default=PriorityChoices.MEDIUM,
        help_text="Priority choice field",
    )

    # JSON Field
    json_field = models.JSONField(help_text="JSONField example", null=True, blank=True, default=dict)

    # UUID Field (inherited from BaseModel)
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Relationships
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="test_models",
        help_text="ForeignKey example",
    )
    author = models.OneToOneField(
        Author,
        on_delete=models.CASCADE,
        related_name="test_model",
        help_text="OneToOneField example",
        null=True,
        blank=True,
    )
    tags = models.ManyToManyField(Tag, related_name="test_models", help_text="ManyToManyField example", blank=True)

    # Additional Fields
    rating = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Rating with validators",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Test Model"
        verbose_name_plural = "Test Models"
        ordering = ["-created_at"]

    def __str__(self):
        return f"TestModel: {self.char_field}"


# Nested Relationship Models
class Company(BaseModel):
    """Company model for nested relationship testing"""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    founded_date = models.DateField(null=True, blank=True)
    is_public = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name


class Department(BaseModel):
    """Department model for nested relationship testing"""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="departments")
    manager = models.ForeignKey(
        "Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments",
    )

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"

    def __str__(self):
        return f"{self.name} ({self.company.name})"


class Employee(BaseModel):
    """Employee model for nested relationship testing"""

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    # Relationships
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="employees")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="employees")
    manager = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="subordinates")
    skills = models.ManyToManyField(Tag, related_name="employees", blank=True)

    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Project(BaseModel):
    """Project model for complex relationship testing"""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    priority = models.CharField(max_length=20, choices=PriorityChoices.choices, default=PriorityChoices.MEDIUM)

    # Relationships
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="projects")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="projects", null=True, blank=True)
    manager = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="managed_projects", null=True, blank=True,
    )
    team_members = models.ManyToManyField(Employee, related_name="projects", blank=True)
    tags = models.ManyToManyField(Tag, related_name="projects", blank=True)

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Task(BaseModel):
    """Task model for deep nested relationship testing"""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    priority = models.CharField(max_length=20, choices=PriorityChoices.choices, default=PriorityChoices.MEDIUM)

    # Relationships
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    assigned_to = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="assigned_tasks")
    created_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="created_tasks")
    tags = models.ManyToManyField(Tag, related_name="tasks", blank=True)

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["due_date", "priority"]

    def __str__(self):
        return self.title


# Simple Models for Basic Testing
class SimpleModel(BaseModel):
    """Simple model for basic CRUD testing"""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Simple Model"
        verbose_name_plural = "Simple Models"

    def __str__(self):
        return self.name


class RelatedModel(BaseModel):
    """Related model for relationship testing"""

    name = models.CharField(max_length=255)
    simple_model = models.ForeignKey(SimpleModel, on_delete=models.CASCADE, related_name="related_models")

    class Meta:
        verbose_name = "Related Model"
        verbose_name_plural = "Related Models"

    def __str__(self):
        return f"{self.name} (related to {self.simple_model.name})"
