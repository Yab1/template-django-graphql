import strawberry
import strawberry_django

from core.users.models import User


@strawberry_django.type(User, description="User account")
class AppUserType:
    id: strawberry.auto
    email: strawberry.auto
    first_name: strawberry.auto
    last_name: strawberry.auto
    is_active: strawberry.auto
    is_staff: strawberry.auto
    is_superuser: strawberry.auto
    phone_number: str
