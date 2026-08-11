import hashlib
from django.db import models

class TranslationCache(models.Model):
    string_hash = models.CharField(max_length=64, db_index=True)
    source_text = models.TextField()
    target_lang = models.CharField(max_length=10)
    translated_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('string_hash', 'target_lang')
        indexes = [
            models.Index(fields=['string_hash', 'target_lang']),
        ]

    def __str__(self):
        return f'{self.target_lang}: {self.source_text[:50]}'
