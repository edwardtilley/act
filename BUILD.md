# Advance Party — Django Storefront Build Spec

**Slug:** `advance`
**Dev port:** 5105
**Prod port:** 5205

Build a complete Django project at `~/projects/advance/` following the
hub's standard conventions.  The hub has already registered this store and
allocated its ports; once the project is built and running, the hub will
probe `/api/health` to confirm the store is live.

---

## Project structure

```
~/projects/advance/
  manage.py
  core/                     # settings package (Django convention)
    __init__.py
    settings.py
    urls.py
    wsgi.py
    asgi.py
  apps/
    __init__.py
    api/
      __init__.py
      apps.py
      views.py              # /api/health endpoint
      urls.py
    store_config/
      __init__.py
      apps.py
      models.py             # StoreConfig, JournalEntry, JournalLine
      views.py              # /setup, /transactions, /invoices
      urls.py
      admin.py
    ai_pm/
      __init__.py
      apps.py
      views.py              # AI Project Manager proxy
      urls.py
    authentication/
      __init__.py
      apps.py
      models.py             # User model
      views.py              # login, register
      urls.py
      admin.py
  templates/
    layouts/base.html       # Soft UI Dashboard shell
    pages/
      index.html
      financial_reports.html
      transactions.html
      invoices.html
      setup.html
      api_center.html
      pricing.html
      checkout.html
      ai_pm.html
  static/                   # Soft UI Dashboard assets
  media/
  requirements.txt
  .env.example
  README.md
```

---

## Conventions

1. **Settings package**: `core/` (NOT `config/`).
2. **Sub-apps**: under `apps/` with `apps/__init__.py` (empty).
3. **UI theme**: **Soft UI Dashboard (Free, BS5)** — clone from
   https://github.com/creativetimofficial/soft-ui-dashboard and adapt
   templates.  Reference the Flask scaffold at
   `~/projects/autoresume/` for the theme structure.
4. **Database**: SQLite by default (`core/settings.py`).
5. **Python**: 3.10+.

---

## Required features

### 1. `/api/health` (apps/api)
Return JSON:
``json
{"app": "advance", "status": "up", "version": "1.0.0", "datetime_utc": "<now-iso>"}
``

### 2. Mall-GL mirroring (apps/store_config)
Models:
- **StoreConfig** — singleton (get_solo()). Fields: `mall_gl_enabled`,
  `hub_callback_url`, `business_id`, `mirror_path`.
- **JournalEntry** — fields: `entry_date`, `description`, `posted`,
  `mirrored_to_hub`, `mirror_error`, `source_journal_entry_id`,
  `created_at_utc`.
- **JournalLine** — FK to JournalEntry. Fields: `account_id`, `debit`,
  `credit`, `memo`.

Views:
- `/setup` — POST form to toggle mall_gl_enabled + set callback/business_id.
- `/transactions` — POST to create a JournalEntry+Line, then best-effort
  POST mirror to `{hub_callback_url}{mirror_path}`. Never abort the local
  write on mirror failure; log error to `mirror_error`.
- `/invoices` — list subscription invoices (demo stubs for now).

### 3. AI Project Manager (apps/ai_pm)
A thin proxy that POSTs to the hub's AI PM endpoint.  The hub provides:
- `/api/hub/ai/chat` — POST with `{"message": ..., "thread_id": ..., "app_id": "advance"}`
Simple chat UI at `/ai-pm/`.

### 4. Authentication (apps/authentication)
- User model with `id`, `username`, `email`, `password_hash`, `is_admin`.
- Login/register/logout views.
- Session-based auth using Django's built-in auth system.

### 5. Front-end pages (Soft UI Dashboard)
All pages use `templates/layouts/base.html` extending Soft UI:
- **/** → index/home
- **/financial-reports** → stub with tabbed Trial Balance / P&L / Balance Sheet / Cash Flow
- **/api-center** → API docs stub
- **/pricing** → pricing page stub
- **/checkout** → cart + payment provider list (read from a PaymentProvider model if it exists, else stub)
- **/ai-pm** → AI PM chat interface

---

## Getting started instructions (for the developer)

```bash
cd ~/projects/advance
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 0.0.0.0:5105
```

The hub will probe `/api/health` on port 5105 and mark this store
online once it responds with `{"status": "up"}`.
