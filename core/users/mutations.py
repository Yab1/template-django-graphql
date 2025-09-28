import strawberry
from gqlauth.user import arg_mutations as auth_mutations


@strawberry.type
class UsersMutation:
    # Authenticated mutations
    update_account = auth_mutations.UpdateAccount.field
    password_change = auth_mutations.PasswordChange.field

    # Public mutations
    sign_in = auth_mutations.ObtainJSONWebToken.field
    sign_up = auth_mutations.Register.field
    password_reset = auth_mutations.PasswordReset.field
    password_set = auth_mutations.PasswordSet.field
    refresh_token = auth_mutations.RefreshToken.field
    revoke_token = auth_mutations.RevokeToken.field
