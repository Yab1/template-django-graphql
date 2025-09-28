from typing import Optional

import strawberry

from core.users.models import User
from core.users.types import AppUserType


@strawberry.type
class UsersQuery:
    @strawberry.field(description="Currently authenticated user")
    def me(self, info) -> Optional[AppUserType]:
        user = info.context.request.user
        if user and user.is_authenticated:
            return user
        return None

    @strawberry.field(description="Get a user by primary key")
    def user(self, id: int) -> Optional[AppUserType]:
        try:
            return User.objects.get(pk=id)
        except User.DoesNotExist:
            return None
