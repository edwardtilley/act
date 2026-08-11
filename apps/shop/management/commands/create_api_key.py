import secrets

from django.core.management.base import BaseCommand, CommandError

from apps.shop.models import ApiKey
from apps.shop.services import hash_key


class Command(BaseCommand):
    help = 'Create a hub shared-services API key. Prints the key ONCE — store it in .env or wipe.env.'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str)
        parser.add_argument('--role', choices=[r[0] for r in ApiKey.ROLES], default='sysop')

    def handle(self, *args, **options):
        key = 'adv_' + secrets.token_urlsafe(32)
        ApiKey.objects.create(name=options['name'], role=options['role'], key_hash=hash_key(key))
        self.stdout.write(self.style.SUCCESS('API key created (shown once):'))
        self.stdout.write(key)
        self.stdout.write(self.style.WARNING('This is the only time the key is shown. Store it in .env now.'))