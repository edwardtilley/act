# Seeds the TranslationCache from translations.json so the static French
# cache is loaded automatically on every deploy (production has no
# LibreTranslate; Railway runs `migrate` on each deploy via Nixpacks).
import json
import os

from django.conf import settings
from django.db import migrations


def seed_translation_cache(apps, schema_editor):
    fixture = os.path.join(settings.BASE_DIR, 'translations.json')
    if not os.path.exists(fixture):
        return
    TranslationCache = apps.get_model('translator', 'TranslationCache')
    with open(fixture) as fh:
        entries = json.load(fh)
    for entry in entries:
        if entry.get('model') != 'translator.translationcache':
            continue
        fields = entry['fields']
        # Keyed on (string_hash, target_lang) so re-runs are idempotent and
        # never collide with rows already present under different PKs.
        TranslationCache.objects.update_or_create(
            string_hash=fields['string_hash'],
            target_lang=fields['target_lang'],
            defaults={
                'source_text': fields['source_text'],
                'translated_text': fields['translated_text'],
            },
        )


def unseed_translation_cache(apps, schema_editor):
    # No-op: leaving seeded cache rows in place on rollback is harmless.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('translator', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_translation_cache, unseed_translation_cache),
    ]
