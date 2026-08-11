import requests
from django.conf import settings

def translate_text(text, target_lang='fr', source_lang='en'):
    if not text or not text.strip():
        return text

    try:
        resp = requests.post(
            f'{settings.LIBRETRANSLATE_URL}/translate',
            json={
                'q': text,
                'source': source_lang,
                'target': target_lang,
                'format': 'text',
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get('translatedText', text)
    except Exception:
        return text


def batch_translate(texts, target_lang='fr', source_lang='en'):
    """Translate multiple strings in one API call, falling back to
    per-string calls if the batch request fails or returns an unusable
    shape (some LibreTranslate builds reject array payloads)."""
    if not texts:
        return texts
    try:
        resp = requests.post(
            f'{settings.LIBRETRANSLATE_URL}/translate',
            json={
                'q': texts,
                'source': source_lang,
                'target': target_lang,
                'format': 'text',
            },
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json().get('translatedText', texts)
        if isinstance(result, list) and len(result) == len(texts):
            return result
        if isinstance(result, str) and len(texts) == 1:
            return [result]
    except Exception:
        pass
    return [translate_text(t, target_lang=target_lang, source_lang=source_lang) for t in texts]
