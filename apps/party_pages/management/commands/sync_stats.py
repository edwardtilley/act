"""Merge new stats.json rows into an existing, persistent database.

With a Railway volume (DATA_DIR), the production DB and images survive
deploys. On every boot this command adds rows that exist in the repository
fixture but not yet in the database — without touching rows that were edited,
renamed, reordered or uploaded in production. Local content therefore stays
authoritative; new dev-authored images are appended.

Run via ensure_database after migrate; safe to run repeatedly.
"""
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.party_pages.models import StatImage, WAOHAnchor


class Command(BaseCommand):
    help = 'Append new StatImage/WAOHAnchor rows from stats.json without overwriting local edits.'

    def handle(self, *args, **options):
        path = getattr(settings, 'STATS_FIXTURE', os.path.join(settings.BASE_DIR, 'stats.json'))
        if not os.path.exists(path):
            self.stdout.write(self.style.WARNING('sync_stats: stats.json not found — skipped'))
            return
        with open(path) as fh:
            entries = json.load(fh)

        stat_entries = [e for e in entries if e.get('model') == 'party_pages.statimage']
        anchor_entries = [e for e in entries if e.get('model') == 'party_pages.waohanchor']

        existing_titles = set(StatImage.objects.values_list('title', flat=True))
        existing_files = set(StatImage.objects.exclude(image_filename='').values_list('image_filename', flat=True))
        max_order = StatImage.objects.order_by('-display_order').values_list('display_order', flat=True).first()
        next_order = (max_order if max_order is not None else -1) + 1

        fixture_titles = {}
        created_stats = 0
        for entry in stat_entries:
            fields = entry.get('fields', {})
            title = fields.get('title', '')
            filename = fields.get('image_filename', '')
            fixture_titles[entry.get('pk')] = title
            if title in existing_titles or (filename and filename in existing_files):
                continue
            StatImage.objects.create(
                title=title,
                image_filename=filename,
                description=fields.get('description', ''),
                keywords=fields.get('keywords', ''),
                links_json=fields.get('links_json', ''),
                active=fields.get('active', True),
                display_order=next_order,
            )
            next_order += 1
            created_stats += 1
            existing_titles.add(title)
            if filename:
                existing_files.add(filename)

        stats_by_title = {row.title: row for row in StatImage.objects.all()}
        created_anchors = 0
        for entry in anchor_entries:
            fields = entry.get('fields', {})
            anchor = fields.get('anchor')
            url = fields.get('url')
            if not anchor or not url:
                continue
            if WAOHAnchor.objects.filter(anchor=anchor, url=url).exists():
                continue
            stat_title = fixture_titles.get(fields.get('stat_image'))
            WAOHAnchor.objects.create(
                name=fields.get('name', ''),
                anchor=anchor,
                url=url,
                category=fields.get('category', ''),
                stat_image=stats_by_title.get(stat_title),
            )
            created_anchors += 1

        self.stdout.write(self.style.SUCCESS(
            f'sync_stats: {created_stats} new image(s), {created_anchors} new anchor(s); '
            'existing rows left untouched'
        ))
