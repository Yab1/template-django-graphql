from django.db import migrations


def create_user_statuses(apps, schema_editor):
    User = apps.get_model("users", "User")
    UserStatus = apps.get_model("gqlauth", "UserStatus")

    for user in User.objects.all():
        if not UserStatus.objects.filter(user_id=user.pk).exists():
            UserStatus.objects.create(user_id=user.pk, verified=False, archived=False)


def noop_reverse(apps, schema_editor):
    # Keep statuses; no-op on reverse to avoid deleting user statuses.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
        ("gqlauth", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_user_statuses, noop_reverse),
    ]


