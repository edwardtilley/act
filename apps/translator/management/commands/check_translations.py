import os
import re
import hashlib
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.translator.libretranslate import batch_translate
from apps.translator.models import TranslationCache


TR_RE = re.compile(r"{%\s*tr\s+['\"]([^'\"]+)['\"]\s*%}")


class Command(BaseCommand):
    help = 'Scan templates for {% tr %} strings and cache any missing translations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--langs',
            default='fr',
            help='Comma-separated target language codes (default: fr)',
        )
        parser.add_argument(
            '--check',
            action='store_true',
            help='Dry-run mode: report coverage without translating. Exits non-zero if coverage < 100%',
        )

    def handle(self, *args, **options):
        langs = options['langs'].split(',')
        is_check = options['check']
        template_dir = settings.BASE_DIR / 'templates'
        strings = set()

        for root, _dirs, files in os.walk(template_dir):
            for f in files:
                if f.endswith('.html'):
                    path = os.path.join(root, f)
                    with open(path) as fh:
                        content = fh.read()
                    for match in TR_RE.finditer(content):
                        strings.add(match.group(1))

        if not strings:
            self.stdout.write(self.style.WARNING('No {% tr %} strings found in templates.'))
            return

        strings = sorted(strings)
        self.stdout.write(f'Found {len(strings)} unique {{% tr %}} strings across templates.')

        total_missing = 0

        for lang in langs:
            existing = set(
                TranslationCache.objects.filter(
                    target_lang=lang,
                    source_text__in=strings,
                ).values_list('source_text', flat=True)
            )
            needed = [s for s in strings if s not in existing]

            coverage = (len(strings) - len(needed)) / len(strings) * 100

            if not needed:
                self.stdout.write(self.style.SUCCESS(
                    f'[{lang}] All {len(strings)} strings cached — coverage 100%'
                ))
                continue

            if is_check:
                self.stdout.write(self.style.ERROR(
                    f'[{lang}] {len(needed)} strings missing — coverage {coverage:.1f}% ({len(strings) - len(needed)}/{len(strings)})'
                ))
                total_missing += len(needed)
                continue

            self.stdout.write(f'[{lang}] Translating {len(needed)} missing strings...')
            results = batch_translate(needed, target_lang=lang)

            objs = []
            for src, tgt in zip(needed, results):
                if tgt == src:
                    continue
                objs.append(TranslationCache(
                    string_hash=hashlib.sha256(src.encode()).hexdigest(),
                    source_text=src,
                    target_lang=lang,
                    translated_text=tgt,
                ))
            failed = len(needed) - len(objs)
            TranslationCache.objects.bulk_create(objs, ignore_conflicts=True)

            total_missing += len(objs)
            self.stdout.write(self.style.SUCCESS(
                f'[{lang}] Cached {len(objs)} new strings — coverage now {coverage:.1f}% ({len(strings) - len(needed)}/{len(strings)})'
            ))

        if total_missing and not is_check:
            self.stdout.write(self.style.SUCCESS(
                f'\nDone. Cached {total_missing} new translations across {len(langs)} language(s).'
            ))
            self.stdout.write('Run `python manage.py dumpdata translator.TranslationCache > translations.json` to export.')

        if is_check and total_missing:
            raise SystemExit(1)
