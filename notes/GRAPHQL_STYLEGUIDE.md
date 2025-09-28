### GraphQL Styleguide (Strawberry + Django)

Adapts your REST styleguide to GraphQL while keeping the same services/selectors core. Uses flat per-app modules (no graphql/ subfolder). For example, patient GraphQL lives in:

- `core/patients/types.py`
- `core/patients/inputs.py`
- `core/patients/queries.py`
- `core/patients/mutations.py`
- `core/patients/loaders.py` (optional)

### Core principles
- Keep resolvers thin: parse inputs, call selectors/services, return objects.
- Business logic stays in services/selectors (same as REST styleguide).
- Evolve schema additively; deprecate instead of breaking.
- Prevent N+1 and control query cost.

### URL and versioning
- Prefer a single endpoint: `/graphql` or `/api/graphql`.
- Optional URL versioning if you plan hard breaks: `/api/v1/graphql/`, `/api/v2/graphql/`.
- Schema versioning (recommended): add fields/types; mark old ones with `deprecation_reason`; remove after clients migrate.

### Project structure (per app, flat)
- Place GraphQL files at the app root:
  - `types.py` — `@strawberry_django.type` object types
  - `inputs.py` — `@strawberry.input` inputs for mutations and filters
  - `queries.py` — `@strawberry.type` query fields that call selectors
  - `mutations.py` — `@strawberry.type` mutation fields that call services
  - `loaders.py` — optional DataLoaders
- Compose app Query/Mutation in `config/schema.py` with `merge_types`.

### Schema configuration
- Enable optimizer: `extensions=[DjangoOptimizerExtension]`.
- Prefer camelCase on the wire: `StrawberryConfig(auto_camel_case=True)`.
- IDs: use UUIDs end-to-end via Strawberry `UUID` scalar.
- Document fields: use `description=`; evolve with `deprecation_reason=`.

### Types and inputs (patient-focused examples)
```python
# core/patients/types.py
import strawberry, strawberry_django
from typing import List
from core.patients.models import Patient, EmergencyContact


@strawberry_django.type(Patient, description="Patient record")
class PatientType:
    id: strawberry.auto
    identity_id: strawberry.auto
    mrn: strawberry.auto
    blood_type: strawberry.auto
    emergency_contacts: List["EmergencyContactType"]


@strawberry_django.type(EmergencyContact)
class EmergencyContactType:
    id: strawberry.auto
    name: strawberry.auto
    relationship: strawberry.auto
    phone_number: strawberry.auto
    address: strawberry.auto
    priority: strawberry.auto
    patient: "PatientType"
```

```python
# core/patients/inputs.py
import uuid, strawberry
from typing import Optional


@strawberry.input
class CreatePatientInput:
    identity_id: uuid.UUID
    blood_type: Optional[str] = None


@strawberry.input
class UpdatePatientInput:
    blood_type: Optional[str] = None
```

### Queries and mutations
- Queries call selectors; mutations call services.
- Validate in services with `full_clean()` or domain validators.

```python
# core/patients/queries.py
import uuid, strawberry, strawberry_django
from typing import List, Optional
from core.patients.types import PatientType
from core.patients.selectors import patient_get, patient_list  # implement in selectors.py


@strawberry.type
class PatientsQuery:
    patients: List[PatientType] = strawberry_django.field()

    @strawberry.field
    def patient(self, id: uuid.UUID) -> Optional[PatientType]:
        return patient_get(id=id)
```

```python
# core/patients/mutations.py
import uuid, strawberry
from core.patients.types import PatientType
from core.patients.inputs import CreatePatientInput, UpdatePatientInput
from core.patients.services import patient_create, patient_update, patient_delete  # implement in services.py
from core.patients.models import Patient


@strawberry.type
class PatientsMutation:
    @strawberry.mutation
    def create_patient(self, input: CreatePatientInput) -> PatientType:
        return patient_create(identity_id=input.identity_id, blood_type=input.blood_type)

    @strawberry.mutation
    def update_patient(self, id: uuid.UUID, input: UpdatePatientInput) -> PatientType:
        patient = Patient.objects.get(pk=id)
        return patient_update(patient=patient, data=input.__dict__)

    @strawberry.mutation
    def delete_patient(self, id: uuid.UUID) -> bool:
        patient = Patient.objects.get(pk=id)
        patient_delete(patient=patient)
        return True
```

### Schema composition
```python
# config/schema.py
import strawberry
from strawberry.tools import merge_types
from strawberry_django.optimizer import DjangoOptimizerExtension
from strawberry.schema.config import StrawberryConfig
from core.patients.queries import PatientsQuery
from core.patients.mutations import PatientsMutation


@strawberry.type
class CommonQuery:
    ping: str = strawberry.field(default="pong")


Query = merge_types("Query", (CommonQuery, PatientsQuery))
Mutation = merge_types("Mutation", (PatientsMutation,))


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[DjangoOptimizerExtension],
    config=StrawberryConfig(auto_camel_case=True),
)
```

### Filtering, ordering, pagination
- Filtering: use `strawberry_django.filters` or accept explicit filter inputs; apply in selectors.
- Ordering: expose sort enums; apply in selectors.
- Pagination: Relay connections for complex needs; otherwise `limit`/`offset` with sane defaults and max limits.

### Error handling
- Standardize errors via a GraphQL error formatter. Map common Django exceptions to `extensions.code` and include field errors for validation.

```python
# config/urls.py (formatter sketch)
from strawberry.django.views import GraphQLView
from graphql import GraphQLError


def error_formatter(error: GraphQLError, debug: bool):
    orig = getattr(error, "original_error", None)
    ext = {"code": "INTERNAL_ERROR", "message": error.message}

    from django.core.exceptions import ValidationError as DjangoValidationError, PermissionDenied
    from django.http import Http404

    if isinstance(orig, DjangoValidationError):
        ext["code"] = "VALIDATION_ERROR"
        ext["fields"] = getattr(orig, "message_dict", {"nonFieldErrors": orig.messages})
    elif isinstance(orig, PermissionDenied):
        ext["code"] = "FORBIDDEN"
    elif isinstance(orig, Http404):
        ext["code"] = "NOT_FOUND"

    return {
        "message": ext["message"],
        "locations": error.locations,
        "path": error.path,
        "extensions": ext,
    }

# urlpatterns → 
# path("api/v1/graphql/", GraphQLView.as_view(schema=schema, graphiql=True, error_formatter=error_formatter))
```

### Authn/Authz
- Access user via `info.context.request.user`.
- Prefer permission checks inside selectors/services. Use lightweight resolver guards for trivial checks.
- Centralize permission utilities; return `FORBIDDEN` on failures.

### Performance
- Keep `DjangoOptimizerExtension` enabled.
- In selectors, use `select_related`/`prefetch_related`; only expose needed fields.
- Use DataLoaders for cross-entity fan-out.
- Consider depth/complexity limits if the client can craft very deep queries.

### Testing
- Unit-test services/selectors as in REST guide.
- GraphQL tests: operation-level tests asserting data and `errors[].extensions`.
- Keep factories; write tests that catch N+1 regressions when possible.

### Documentation and DX
- Add `description=` to types/fields/inputs for schema docs.
- Enable GraphiQL in non-prod.
- Consider frontend codegen (e.g., TypeScript types) from schema.

### Migration/changes policy
- Non-breaking: add fields/types/args.
- Breaking: deprecate first with `deprecation_reason`; remove after a grace period; or ship a new endpoint version (e.g., `/api/v2/graphql/`).

### Patient minimum checklist
- `types.py`: `PatientType`, `EmergencyContactType`.
- `inputs.py`: `CreatePatientInput`, `UpdatePatientInput`.
- `queries.py`: `patient(id)`, `patients(...)` (plus filters/pagination when ready).
- `mutations.py`: `createPatient`, `updatePatient`, `deletePatient`.
- `selectors.py` and `services.py`: mirror REST styleguide responsibilities.

