from django import template
from django.conf import settings
from django.utils import translation
from apps.translator.models import TranslationCache
from apps.translator.libretranslate import translate_text
import hashlib

register = template.Library()

@register.simple_tag(takes_context=True)
def tr(context, text):
    lang = translation.get_language()
    if lang == 'en' or not text:
        return text

    string_hash = hashlib.sha256(text.encode()).hexdigest()

    cached = TranslationCache.objects.filter(
        string_hash=string_hash, target_lang=lang
    ).first()
    if cached:
        return cached.translated_text

    translated = translate_text(text, target_lang=lang)
    if translated and translated != text:
        TranslationCache.objects.update_or_create(
            string_hash=string_hash,
            target_lang=lang,
            defaults={'source_text': text, 'translated_text': translated},
        )
    return translated or text
