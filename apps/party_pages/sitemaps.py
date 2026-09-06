from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Riding


class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'

    def items(self):
        # Public, indexable pages only — no dashboard/profile/stateditor.
        return [
            ('index', 1.0),
            ('map', 0.8),
            ('candidates', 0.9),
            ('policies', 0.9),
            ('candidate_join', 0.7),
            ('member_join', 0.7),
            ('certifications', 0.6),
            ('pricing', 0.5),
            ('stats', 0.5),
        ]

    def location(self, item):
        return reverse(item[0])

    def priority(self, item):
        return item[1]


class RidingSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return Riding.objects.exclude(
            candidate_url__isnull=True
        ).exclude(candidate_url='').only('candidate_url')

    def location(self, obj):
        return reverse('riding_office', kwargs={'slug': obj.candidate_url})
