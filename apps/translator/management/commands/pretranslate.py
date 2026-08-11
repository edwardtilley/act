from django.core.management.base import BaseCommand
from django.conf import settings
from apps.translator.libretranslate import batch_translate
from apps.translator.models import TranslationCache
import hashlib


class Command(BaseCommand):
    help = 'Pre-translate all registered strings into target languages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--langs',
            default='fr',
            help='Comma-separated target language codes (default: fr)',
        )
        parser.add_argument(
            '--strings',
            nargs='+',
            required=True,
            help='Strings to pre-translate',
        )

    def handle(self, *args, **options):
        langs = options['langs'].split(',')
        strings = options['strings']

        for lang in langs:
            existing = set(
                TranslationCache.objects.filter(
                    target_lang=lang,
                    source_text__in=strings,
                ).values_list('source_text', flat=True)
            )
            needed = [s for s in strings if s not in existing]

            if not needed:
                self.stdout.write(f'All {len(strings)} strings already cached for {lang}')
                continue

            self.stdout.write(f'Translating {len(needed)} strings into {lang}...')
            results = batch_translate(needed, target_lang=lang)

            objs = []
            for src, tgt in zip(needed, results):
                objs.append(TranslationCache(
                    string_hash=hashlib.sha256(src.encode()).hexdigest(),
                    source_text=src,
                    target_lang=lang,
                    translated_text=tgt,
                ))
            TranslationCache.objects.bulk_create(objs, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(f'Cached {len(objs)} translations for {lang}'))
