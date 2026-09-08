"""Upsert the default chart of accounts (idempotent)."""

from django.core.management.base import BaseCommand

from apps.ledger.default_coa import seed_chart_of_accounts


class Command(BaseCommand):
    help = 'Upsert the default chart of accounts for the Advance store ledger.'

    def handle(self, *args, **options):
        created = seed_chart_of_accounts()
        self.stdout.write(self.style.SUCCESS(
            f'Chart of accounts OK — {created} account(s) newly created.'
        ))
