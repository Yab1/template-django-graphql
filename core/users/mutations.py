import strawberry
from gqlauth.user import arg_mutations as auth_mutations


@strawberry.type
class UsersMutation:
    # Authenticated mutations
    update_account = auth_mutations.UpdateAccount.field
    password_change = auth_mutations.PasswordChange.field

    # Public mutations
    token_auth = auth_mutations.ObtainJSONWebToken.field
    register = auth_mutations.Register.field
    password_reset = auth_mutations.PasswordReset.field
    password_set = auth_mutations.PasswordSet.field
    refresh_token = auth_mutations.RefreshToken.field
    revoke_token = auth_mutations.RevokeToken.field
