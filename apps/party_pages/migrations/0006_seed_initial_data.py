# Seeds Riding and Certification rows from the repo fixtures on deploy.
# Runs with `migrate` on every deploy regardless of builder/start-command
# configuration (Railway/Railpack may ignore nixpacks.toml), so this is the
# reliable bootstrap path. Keyed on unique natural fields so re-runs and
# existing rows are safe (upsert, never duplicates).
import json
import os

from django.conf import settings
from django.db import migrations


def _seed(apps, model_name, fixture, key_field):
    path = os.path.join(settings.BASE_DIR, fixture)
    if not os.path.exists(path):
        return
    Model = apps.get_model('party_pages', model_name)
    # Fixtures are exported from the LATEST model; on a fresh DB this migration
    # runs before later schema migrations, so drop any fields that don't exist
    # yet at this point in history (e.g. candidate_status, added in 0008).
    valid_fields = {f.name for f in Model._meta.get_fields()}
    with open(path) as fh:
        entries = json.load(fh)
    for entry in entries:
        if entry.get('model') != f'party_pages.{model_name.lower()}':
            continue
        fields = {k: v for k, v in entry['fields'].items() if k in valid_fields}
        if not fields.get(key_field):
            continue
        Model.objects.update_or_create(**{key_field: fields[key_field]}, defaults=fields)


def seed_initial_data(apps, schema_editor):
    _seed(apps, 'Riding', 'ridings.json', 'candidate_url')
    _seed(apps, 'Certification', 'certifications.json', 'title')


def unseed_initial_data(apps, schema_editor):
    # No-op: leaving seeded rows in place on rollback is harmless.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('party_pages', '0005_riding_candidate_certification_riding_director_name_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_initial_data, unseed_initial_data),
    ]
