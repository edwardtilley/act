# Seeds StatImage + WAOHAnchor (/stats page data) from stats.json on deploy.
# Runs with `migrate` on every deploy; upserts on natural keys so re-runs
# and existing rows are safe (never duplicates).
import json
import os

from django.conf import settings
from django.db import migrations


def seed_stats(apps, schema_editor):
    path = os.path.join(settings.BASE_DIR, 'stats.json')
    if not os.path.exists(path):
        return
    StatImage = apps.get_model('party_pages', 'StatImage')
    WAOHAnchor = apps.get_model('party_pages', 'WAOHAnchor')
    # Keep only fields that exist at this point in migration history — the
    # fixture is exported from the latest model which may be newer than this
    # migration's schema when a fresh DB is bootstrapped.
    stat_fields = {f.name for f in StatImage._meta.get_fields()}
    anchor_fields = {f.name for f in WAOHAnchor._meta.get_fields()}
    with open(path) as fh:
        entries = json.load(fh)

    # StatImages first — anchors reference them by (fixture) PK.
    pk_map = {}
    for entry in entries:
        if entry.get('model') != 'party_pages.statimage':
            continue
        fields = {k: v for k, v in entry['fields'].items() if k in stat_fields}
        # Natural key: (title, image_filename) — titles alone are not unique.
        obj, _ = StatImage.objects.update_or_create(
            title=fields.pop('title'),
            image_filename=fields.pop('image_filename'),
            defaults=fields)
        pk_map[entry['pk']] = obj.pk

    for entry in entries:
        if entry.get('model') != 'party_pages.waohanchor':
            continue
        fields = {k: v for k, v in entry['fields'].items() if k in anchor_fields}
        anchor_fk = fields.pop('stat_image', None)
        fields['stat_image_id'] = pk_map.get(anchor_fk) if anchor_fk else None
        # natural key: (anchor, url) — matches the model's unique_together
        search = {'anchor': fields.pop('anchor'), 'url': fields.pop('url')}
        WAOHAnchor.objects.update_or_create(**search, defaults=fields)


def unseed_stats(apps, schema_editor):
    # No-op: leaving seeded rows in place on rollback is harmless.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('party_pages', '0006_seed_initial_data'),
    ]

    operations = [
        migrations.RunPython(seed_stats, unseed_stats),
    ]
