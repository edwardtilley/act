"""Upsert translations.json into a persistent production database.

On a fresh database migration translator.0002 seeds the cache once. With a
Railway volume the DB persists across deploys, so later additions to
translations.json would otherwise never reach production. This command keeps
the cache in sync with the repository copy (repository is authoritative).
"""
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.translator.models import TranslationCache


class Command(BaseCommand):
    help = 'Upsert translations.json into TranslationCache (persistent DBs).'

    def handle(self, *args, **options):
        path = os.path.join(settings.BASE_DIR, 'translations.json')
        if not os.path.exists(path):
            self.stdout.write(self.style.WARNING('sync_translations: translations.json not found — skipped'))
            return
        with open(path) as fh:
            entries = json.load(fh)
        count = 0
        for entry in entries:
            if entry.get('model') != 'translator.translationcache':
                continue
            fields = entry.get('fields', {})
            TranslationCache.objects.update_or_create(
                string_hash=fields.get('string_hash', ''),
                target_lang=fields.get('target_lang', ''),
                defaults={
                    'source_text': fields.get('source_text', ''),
                    'translated_text': fields.get('translated_text', ''),
                },
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(
            f'sync_translations: {count} entries synced from translations.json'
        ))
