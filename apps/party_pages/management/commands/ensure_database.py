"""
Idempotent database bootstrap for deploys — safe to run on every start.

Runs in production (Railway) via the nixpacks.toml start command:
    python manage.py ensure_database && gunicorn core.wsgi ...

On a fresh/empty database it:
  1. Runs `migrate` (creates all tables; translator.0002 also seeds the
     French TranslationCache from translations.json)
  2. Seeds Riding rows from ridings.json (only if the table is empty)
  3. Seeds Certification rows from certifications.json (only if empty)
  4. Creates an admin superuser if DJANGO_SUPERUSER_USERNAME/PASSWORD
     are set in the environment and no superuser exists yet

Re-running against an existing database changes nothing (no duplicates,
no overwrites), so it is safe as a deploy hook.
"""
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Ensure the database exists and is seeded with minimal production data (idempotent).'

    def handle(self, *args, **options):
        # 1. Schema — creates all tables on a fresh database; no-op otherwise.
        self.stdout.write('ensure_database: running migrations...')
        call_command('migrate', interactive=False, verbosity=0)
        self.stdout.write(self.style.SUCCESS('ensure_database: migrations OK'))

        # 2+3. Minimal content fixtures — only loaded into empty tables.
        self._seed_fixture(
            app_label='party_pages', model_name='Riding',
            fixture='ridings.json',
        )
        self._seed_fixture(
            app_label='party_pages', model_name='Certification',
            fixture='certifications.json',
        )

        # 4. Optional admin user from env vars (never overwrites).
        self._ensure_superuser()

        self.stdout.write(self.style.SUCCESS('ensure_database: done'))

    def _seed_fixture(self, app_label, model_name, fixture):
        from django.apps import apps
        model = apps.get_model(app_label, model_name)
        count = model.objects.count()
        if count:
            self.stdout.write(f'ensure_database: {model_name} has {count} rows — seed skipped')
            return
        from django.conf import settings
        path = os.path.join(settings.BASE_DIR, fixture)
        if not os.path.exists(path):
            self.stdout.write(self.style.WARNING(
                f'ensure_database: {fixture} not found — {model_name} left empty'))
            return
        call_command('loaddata', path, verbosity=0)
        self.stdout.write(self.style.SUCCESS(
            f'ensure_database: seeded {model.objects.count()} {model_name} rows from {fixture}'))

    def _ensure_superuser(self):
        username = os.getenv('DJANGO_SUPERUSER_USERNAME')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD')
        if not username or not password:
            self.stdout.write('ensure_database: no DJANGO_SUPERUSER_* env vars — superuser step skipped')
            return
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write('ensure_database: a superuser already exists — skipped')
            return
        User.objects.create_superuser(
            username=username,
            email=os.getenv('DJANGO_SUPERUSER_EMAIL', ''),
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(
            f'ensure_database: created superuser "{username}"'))
