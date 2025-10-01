import shutil
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a new app under core/<app_name> and scaffold GraphQL files"

    def add_arguments(self, parser):
        parser.add_argument("app_name", type=str, help="Name of the new app, e.g., reports")
        parser.add_argument(
            "--register",
            action="store_true",
            help="Attempt to register app in settings LOCAL_APPS (config/django/base.py)",
        )

    def handle(self, *args, **options):
        app_name: str = options["app_name"].strip()
        if not app_name.isidentifier():
            raise CommandError(f"Invalid app name: {app_name!r}")

        project_root = Path(settings.BASE_DIR)
        core_dir = project_root / "core"
        app_dir = core_dir / app_name

        if app_dir.exists():
            raise CommandError(f"App directory already exists: {app_dir}")

        app_dir.mkdir(parents=True, exist_ok=False)

        # Run startapp into the created directory
        # Equivalent to: python manage.py startapp <app_name> core/<app_name>
        try:
            subprocess.run(
                [
                    sys.executable,
                    "manage.py",
                    "startapp",
                    app_name,
                    str(app_dir),
                ],
                check=True,
                cwd=str(project_root),
            )
        except subprocess.CalledProcessError as exc:
            # Clean up the directory if startapp failed
            if app_dir.exists():
                shutil.rmtree(app_dir)
            raise CommandError("Django startapp failed") from exc

        # Fix apps.py: set name = "core.<app_name>"
        apps_py = app_dir / "apps.py"
        if apps_py.exists():
            content = apps_py.read_text()
            lines = content.splitlines()
            new_lines = []
            replaced = False
            for line in lines:
                if line.strip().startswith("name = "):
                    new_lines.append(f'    name = "core.{app_name}"')
                    replaced = True
                else:
                    new_lines.append(line)
            if not replaced:
                # Try appending under the AppConfig class if not found
                new_lines.append(f'    name = "core.{app_name}"')
            apps_py.write_text("\n".join(new_lines) + "\n")

        # Remove tests.py and views.py if present
        for fname in ("tests.py", "views.py"):
            fpath = app_dir / fname
            if fpath.exists():
                fpath.unlink()

        # Ensure migrations package with __init__.py
        migrations_dir = app_dir / "migrations"
        migrations_dir.mkdir(exist_ok=True)
        (migrations_dir / "__init__.py").touch(exist_ok=True)

        # Create GraphQL-related empty modules
        for fname in ("inputs.py", "types.py", "mutations.py", "queries.py"):
            (app_dir / fname).touch(exist_ok=True)

        # Add to LOCAL_APPS if requested
        if options.get("register"):
            settings_path = project_root / "config" / "django" / "base.py"
            if settings_path.exists():
                text = settings_path.read_text()
                marker = "LOCAL_APPS = ["
                if marker in text and f"core.{app_name}.apps." not in text and f"core.{app_name}" not in text:
                    # Insert after first item (we prefer app config class style)
                    # Derive AppConfig class name from app_name (e.g., reports -> ReportsConfig)
                    app_config_class = "".join(part.capitalize() for part in app_name.split("_")) + "Config"
                    app_config_path = f"core.{app_name}.apps.{app_config_class}"
                    new_text = text.replace(
                        marker + "\n",
                        marker + f'\n    "{app_config_path}",\n',
                        1,
                    )
                    settings_path.write_text(new_text)

        self.stdout.write(self.style.SUCCESS(f"App created at {app_dir}"))
