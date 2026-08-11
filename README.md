# Advance Party of Canada

A high-impact, wildly graphic, moving-video political party website built with Django and Soft UI Dashboard.

## Quick Start

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:5105
```

## Routes

| Route | Page |
|-------|------|
| `/` | Landing (classic hero) |
| `/index1` | Landing (fullscreen video) |
| `/index2` | Landing (particle canvas) |
| `/index3` | Landing (card mosaic) |
| `/map` | Interactive Canada riding map |
| `/candidates` | DataTables searchable candidates |
| `/policies` | Policy accordion dashboard |
| `/candidate-join` | Candidate sign-up |
| `/member-join` | Member sign-up |
| `/certifications` | CS Certifications |
| `/api/health` | Health check (JSON) |
| `/auth/login` | Login |
| `/auth/register` | Register |
| `/admin/` | Django admin |

## Translation (EN→FR)

The site uses a self-hosted [LibreTranslate](https://libretranslate.com) Docker container for automatic English-to-French translation.

### Setup
```bash
sudo docker compose up -d
curl http://localhost:5030/translate -X POST -H "Content-Type: application/json" \
  -d '{"q":"Hello","source":"en","target":"fr"}'
# → {"translatedText":"Bonjour"}
```

### Workflow before deploying to PythonAnywhere

LibreTranslate won't be available in production, so you must pre-cache all translations and export them:

```bash
# 1. Populate cache — scans templates, translates missing strings
python manage.py check_translations

# 2. Verify 100% coverage before deploying (exits 1 if incomplete)
python manage.py check_translations --check

# 3. Export to fixture file
python manage.py dumpdata translator.TranslationCache > translations.json

# 4. Deploy translations.json, then on production:
python manage.py loaddata translations.json
```

In production, `{% tr %}` serves cached French text. Uncacheable strings fall back to English.

### Usage in templates
```django
{% load translate_en %}
<p>{% tr "This text will be translated" %}</p>
```

Add `?lang=fr` to any URL to switch to French. The nav includes EN/FR toggle links.

## Colour Palette

- **Primary:** Red `#CC0000`
- **Secondary:** White `#FFFFFF`
- **Accent 1:** Green `#00AA00`
- **Accent 2:** Blue `#0055CC`
- **Text:** Dark `#1A1A1A`
- **Background:** Off-white `#F5F5F5`
