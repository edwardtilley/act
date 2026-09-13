# Advance Party of Canada — AGENTS Architecture

## 1. Project Overview

A Django-based political party website for **The Advance Party of Canada**.
High‑impact, wildly graphic, moving‑video, parallax‑scrolling front‑end with a
Soft UI Dashboard admin back‑end.

**Stack:** Django 5.x, SQLite, Soft UI Dashboard (BS5), DataTables.net,
Google Maps / Leaflet.js, Font Awesome 6.

**Port:** 5105 (dev), 5205 (prod)

---

## 2. Directory Structure

```
~/projects/advance/
├── AGENTS.md                     # This architecture document
├── BUILD.md                      # Original build spec
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── core/                         # Django settings package
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── __init__.py
│   ├── api/                      # Health-check endpoint
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── authentication/           # Login / register / logout
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── admin.py
│   ├── party_pages/              # All political-party page views
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── admin.py
│   └── ledger/                    # Double-entry GL + financial reports (own books)
│       ├── __init__.py
│       ├── apps.py
│       ├── models.py             # Account, JournalEntry, JournalLine
│       ├── accounting.py         # trial balance / balance sheet / P&L / cash flow math
│       ├── default_coa.py        # DEFAULT_CHART_OF_ACCOUNTS seed
│       ├── views.py              # staff-only journal CRUD + report pages
│       ├── urls.py               # /admin-financial/... (NOT /admin/ — Django's)
│       └── migrations/
├── templates/
│   ├── layouts/
│   │   └── base.html             # Soft UI Dashboard shell
│   ├── includes/
│   │   ├── head.html
│   │   ├── scripts.html
│   │   ├── navigation.html
│   │   ├── sidebar.html
│   │   ├── footer.html
│   │   └── configurator.html
│   └── pages/
│       ├── index.html            # Landing variant A (classic hero)
│       ├── index1.html           # Landing variant B (fullscreen video)
│       ├── index2.html           # Landing variant C (particle canvas)
│       ├── index3.html           # Landing variant D (card mosaic)
│       ├── map.html              # Map of Canada / ridings
│       ├── candidates.html       # DataTables list of ridings + candidates
│       ├── policies.html         # Policy accordion dashboard
│       ├── candidate_join.html   # Candidate sign-up form
│       ├── member_join.html      # Party member sign-up form
│       └── certifications.html   # CS Certifications
├── static/
│   └── assets/
│       ├── css/                  # Soft UI Dashboard CSS + custom.css
│       ├── js/                   # Soft UI Dashboard JS
│       ├── vendor/               # jQuery, DataTables, etc.
│       ├── img/                  # Images, favicon
│       └── video/                # Hero background video clips
└── media/
```

---

## 3. Colour Palette

| Role         | Colour      | Hex       | Usage                                  |
|-------------|-------------|-----------|----------------------------------------|
| Primary     | Advance Red | `#CC0000` | Hero backgrounds, buttons, headings    |
| Secondary   | White       | `#FFFFFF` | Text on dark, card backgrounds          |
| Accent 1    | Green       | `#00AA00` | CTA buttons, highlight accents         |
| Accent 2    | Blue        | `#0055CC` | Links, secondary CTAs                  |
| Text        | Dark        | `#1A1A1A` | Body text on light backgrounds         |
| Light Bg    | Off-white   | `#F5F5F5` | Section backgrounds                    |

---

## 4. Page Inventory & Routes

| Route                         | Template                   | Description                                      |
|-------------------------------|----------------------------|--------------------------------------------------|
| `/`                           | `pages/index.html`         | Landing variant A                                |
| `/index1`                     | `pages/index1.html`        | Landing variant B                                |
| `/index2`                     | `pages/index2.html`        | Landing variant C                                |
| `/index3`                     | `pages/index3.html`        | Landing variant D                                |
| `/map`                        | `pages/map.html`           | Interactive Canada map with riding data          |
| `/candidates`                 | `pages/candidates.html`    | DataTables searchable riding/candidate list      |
| `/policies`                   | `pages/policies.html`      | Policy accordion dashboard                       |
| `/candidate-join`             | `pages/candidate_join.html`| Candidate sign-up form                           |
| `/member-join`                | `pages/member_join.html`   | Party member sign-up form                        |
| `/certifications`             | `pages/certifications.html`| CS Certifications info + application             |
| `/admin-candidates`           | `pages/admin_candidates.html`| Candidate CRUD (DataTables, status pull-down, detail/edit/delete modals) |
| `/admin-financial/journal-entries` | `ledger/journal_entries.html`| Double-entry journal CRUD (staff; debits=credits enforced) |
| `/admin-financial/reports/trial-balance` | `ledger/trial_balance.html` | Trial balance as-of a date |
| `/admin-financial/reports/balance-sheet` | `ledger/balance_sheet.html` | Assets = Liabilities + Equity as-of |
| `/admin-financial/reports/p-and-l` | `ledger/p_and_l.html`       | Profit & Loss for a date window |
| `/admin-financial/reports/cash-flow` | `ledger/cash_flow.html`  | Simplified indirect cash flow (Cash account 1000) |
| `/api/health`                 | JSON response              | Health check endpoint                            |
| `/auth/login`                 | auth template              | Login page                                       |
| `/auth/register`              | auth template              | Registration page                                |
| `/auth/logout`                | redirect                   | Logout                                           |

---

## 5. Data Models

### Riding (party_pages/models.py)
- `id` (AutoField)
- `province` (CharField — province name)
- `region` (CharField — e.g. "Western Canada", "Atlantic")
- `riding_name` (CharField — official riding name)
- `riding_number` (CharField — Elections Canada number)
- `mp_name` (CharField — current MP name, nullable)
- `mp_party` (CharField — party affiliation, nullable)
- `mpp_name` (CharField — provincial rep, nullable)
- `mpp_party` (CharField — nullable)
- `latitude` (FloatField, nullable)
- `longitude` (FloatField, nullable)
- `candidate_name` (CharField — Advance Party candidate, nullable; **blank when no candidate is running** — never seed placeholder names)
- `candidate_photo` (ImageField, nullable)
- `candidate_bio` (TextField, nullable)
- `candidate_url` (SlugField, unique — natural key for fixture seeding; kept even without a candidate)
- `candidate_status` (current | prior | applied, blank default)
- `candidate_accepted_at` (DateField, nullable — shown humanized via django.contrib.humanize)
- `candidate_accepted_by` (CharField — accepting official)
- `candidate_elected` (BooleanField)
- Managed via the `/admin-candidates` CRUD page (Admin sidebar); migration 0008 purged the fabricated seed candidates

### JoinApplication (party_pages/models.py)
- `id`, `application_type` (candidate|member)
- `first_name`, `last_name`, `email`, `phone`
- `address`, `city`, `province`, `postal_code`
- `message` (TextField)
- `submitted_at` (DateTimeField)

### Certification (party_pages/models.py)
- `id`, `title`, `description`, `duration`, `level`
- `active` (BooleanField)

### CertificationApplication (party_pages/models.py)
- `id`, `certification` (FK)
- `first_name`, `last_name`, `email`, `phone`
- `experience`, `motivation` (TextField)
- `submitted_at` (DateTimeField)

### Account / JournalEntry / JournalLine (apps/ledger/models.py)
The store's own double-entry books (advance is one store — no per-store scoping
field). Seeded with the default chart of accounts in `default_coa.py` (19
accounts, codes 1000–5900) via `ledger.0001` data migration on every deploy.

- **Account**: `code` (unique), `name`, `account_type` (asset|liability|equity|revenue|expense), `normal_balance` (debit|credit), `is_active`.
- **JournalEntry**: `entry_date`, `description`, `reference`, `posted`, `posted_at`, `created_by`, `hub_committed`, `hub_pushed_at` (for hub roll-up), timestamps.
- **JournalLine**: `journal_entry` (FK), `account` (FK), `debit`, `credit`, `memo`. Exactly one side is nonzero.

Reports: `apps/ledger/accounting.py` models trial balance (net follows
`normal_balance`), balance sheet (assets = liabilities + equity, where equity
includes current-period net income), P&L (revenue credit−debit / expense
debit−credit over a window), and a simplified indirect cash flow that tracks
the Cash account `1000`. All report math excludes unposted drafts.

**Hub roll-up:** posted journal entries carry `hub_committed`/`hub_pushed_at`
so the shared hub can aggregate this store's transactions — the actual push is
a hub-side concern (see §11; request via a hub change request, never edit the
hub). Only staff/superusers may view or edit.

---

## 6. Soft UI Dashboard Integration

- Clone the Soft UI Dashboard Free (BS5) CSS/JS into `static/assets/`
- Adapt the Flask `base.html` from autoresume to Django's `{% static %}` tag
- All pages extend `layouts/base.html` or use full-width landing layouts
- DataTables.net integrated for the candidates table
- Vendor libs (jQuery, DataTables, Popper, Bootstrap) in `static/assets/vendor/`

---

## 7. Map Implementation

Use **Leaflet.js** (lightweight open-source map library) with OpenStreetMap tiles:
- Display Canada with province/territory outlines
- Mark riding centers with GeoJSON data
- Click on a marker to show MP/MPP/candidate info in a popup
- Filters by province, region

Fallback: embed Google My Maps iframe.

---

## 8. Landing Page Variants

1. **index.html** — Classic hero: full-width red gradient overlay on video bg, CTA buttons, feature cards below
2. **index1.html** — Fullscreen video hero with bold typography overlay, stats counter section
3. **index2.html** — Particle/canvas animated background, glitch text effect, split-screen layout
4. **index3.html** — Card mosaic grid with hover zoom, diagonal section dividers, testimonial carousel

All variants share: nav bar, footer, consistent colour palette, parallax scrolling sections.

---

## 9. Translation System

Uses **LibreTranslate** (self-hosted via Docker) for on-the-fly EN→FR translation.

### Architecture

| Component | File | Role |
|-----------|------|------|
| Template tag | `apps/translator/templatetags/translate_en.py` | `{% tr "text" %}` — translates strings in templates |
| API client | `apps/translator/libretranslate.py` | Calls LibreTranslate REST API |
| Middleware | `apps/translator/middleware.py` | Activates language from `?lang=` param or session |
| Cache | `apps/translator/models.py` | `TranslationCache` table stores translated strings |
| Scanner | `apps/translator/management/commands/check_translations.py` | Auto-discovers and caches translations |

### How it works

1. Templates wrap English text with `{% load translate_en %}{% tr "Hello" %}`
2. Visitor clicks **FR** in nav → `?lang=fr` → middleware activates French
3. `{% tr %}` checks `TranslationCache` — if found, serves cached translation
4. On cache miss, calls LibreTranslate, stores result, returns it
5. **Production (PythonAnywhere):** no LibreTranslate available → cache hit serves French; cache miss falls back to English gracefully

### Pre-deployment workflow

```bash
# 1. Ensure LibreTranslate is running
# 2. Scan templates, translate any missing strings, cache them
python manage.py check_translations

# 3. Verify 100% coverage (exits non-zero if incomplete).
#    The scanner caches untranslatable strings (punctuation, phone numbers)
#    as identity entries, so a clean run should always reach 100%.
python manage.py check_translations --check

# 4. Export cache to fixture and commit it
python manage.py dumpdata translator.TranslationCache > translations.json

# 5. Push — production (Railway) seeds the cache automatically:
#    migration translator.0002_seed_translation_cache runs with `migrate`
#    on every deploy and upserts translations.json into TranslationCache.
#    No manual loaddata step needed.
```

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `check_translations --check` exits 1 | New strings added to templates without caching | Run `check_translations` (no `--check`) to translate them |
| English shows instead of French on `?lang=fr` | String not in cache | Re-run `check_translations` and re-export |
| `check_translations` can't reach API | LibreTranslate not running | `sudo docker compose up -d` + verify `curl http://localhost:5030/translate` |
| Stale French after editing English text | Cache still has old translation | Delete cache entries or run `check_translations` (it overwrites on hash match, so edit changes the hash → creates new entry; old ones remain orphaned but harmless) |

### Tracking coverage

```bash
# Template-string count vs cache-entry count should match
grep -rohP "(?<={% tr \")[^\"]+" templates/ | sort -u | wc -l
python -c "from apps.translator.models import TranslationCache; print(TranslationCache.objects.filter(target_lang='fr').count())"
```

---

## 10. Production Database Bootstrap (ensure_database)

Railway's filesystem is ephemeral — the SQLite DB is recreated on every
deploy. `python manage.py ensure_database` (idempotent, safe to run on every
boot) builds a minimal working database from nothing:

1. Runs `migrate` — creates all tables and seeds content via data
   migrations (this is the reliable path: Railway runs `migrate` on every
   deploy regardless of builder/start-command config):
   - `translator.0002` seeds TranslationCache from `translations.json`
   - `party_pages.0006` seeds Riding (`ridings.json`) and Certification
     (`certifications.json`) — upserts by natural key, so re-runs and
     existing rows are safe
   - `party_pages.0007` seeds StatImage + WAOHAnchor (`stats.json`) for
     the /stats page — single fixture, StatImages re-linked first because
     anchors hold FKs to them
2. Seeds **Riding** rows from `ridings.json` (only if the table is empty)
3. Seeds **Certification** rows from `certifications.json` (only if empty)
4. Creates an admin superuser if `DJANGO_SUPERUSER_USERNAME` /
   `DJANGO_SUPERUSER_PASSWORD` are set in Railway Variables and no
   superuser exists yet

(`ensure_database` steps 2–4 are belt-and-braces on top of the migration
seeding; they are also what makes the command useful when run manually.)

**Gotcha:** fixtures are exported from the *latest* model, but the seed
migrations run against *historical* models. The seeders therefore drop any
fixture fields that don't exist yet in their migration's schema — always keep
that field-filtering in place, or a fresh-DB deploy crashes with
`FieldError` when a remodelled fixture meets an older migration.

**Deploy wiring:** `nixpacks.toml` sets the Railway start command to
`python manage.py ensure_database && gunicorn core.wsgi ...` — so push to
GitHub and the whole chain (build → ensure_database → serve) is automatic.
No dashboard configuration needed beyond env vars.

**Refreshing seed data** after content changes locally:

```bash
python manage.py dumpdata party_pages.Riding --indent 2 > ridings.json
python manage.py dumpdata party_pages.Certification --indent 2 > certifications.json
python manage.py dumpdata party_pages.StatImage party_pages.WAOHAnchor --indent 2 > stats.json
python manage.py dumpdata translator.TranslationCache > translations.json
```

Commit all three fixtures; the next deploy seeds them into a fresh DB.
Never put JoinApplication / CertificationApplication (real user
submissions) into fixtures.

---

## 11. Hub Shared-Services Access Rules (MANDATORY)

The **hub project (`~/projects/hub`)** provides the shared services advance consumes
(hub payment gateway, cart/checkout, financial reporting, MCP surface). It is a
**separate repository with its own owner/operator**. Advance agents **NEVER
write, edit, delete, or commit anything under `~/projects/hub/`** — treat the
hub directory as strictly **read-only** (reading hub code, schemas, and MCP
definitions is allowed and encouraged for integration).

### Requesting hub changes

Any hub change (bug fix, template tweak, feature, API adjustment) must be
requested through the hub's **change-request ticketing** mechanism and may only
be actioned by the hub's owner:

1. **File a ticket via the hub's MCP API** (hub MCP server on port 5001,
   `hub_mcp/server.py`, tool group `change_request_*`):
   - `change_request_submit` — params: `summary` (<300 chars, required),
     `description` (full requested change, required), `ticket_type`
     (`mcp|user_request|other`, default `mcp`), `priority`
     (`low|medium|high|critical`, default `medium`), optional `deadline`,
     `user_name`. Any authenticated agent role may submit.
   - `change_request_list` / `change_request_get` — view tickets (owner-scoped;
     admin sees all).
   - `change_request_recommend` (admin) — writes the hub's recommended solution,
     flips ticket to `in_review`.
   - `change_request_decide` (admin) — approve/reject; the decision + reason
     becomes the audit record for production changes.
2. **Track in the hub UI** at `/hub/changes` (routes in `apps/hub/change_routes.py`).
3. **Wait for the hub owner's approved change** before expecting new behavior;
   do not work around missing hub capabilities by patching hub code locally.

A pending/approved change request (or a concrete blocker that needs one) should
be noted in this repo's session context so the next session remembers to check
the ticket status.

Integration view: advance consumes hub endpoints as an API consumer only —
see `SOP-HUB-INTEGRATION.md` (first-store integration record).

---

## 12. Build Order

1. Create AGENTS.md (this file)
2. Django skeleton: `manage.py`, `core/`, `requirements.txt`
3. Copy Soft UI Dashboard static assets from autoresume
4. Create `apps/api` (health endpoint)
5. Create `apps/authentication` (User model, login/register/logout)
6. Create `apps/party_pages` (models, views, urls)
7. Create `templates/layouts/base.html` + includes (Django-ified)
8. Build 4 landing page templates
9. Build map page
10. Build candidates datatables page
11. Build policies accordion page
12. Build candidate join form page
13. Build member join form page
14. Build certifications page
15. Wire up URLs in `core/urls.py`
16. Verify `python manage.py runserver` works and `/api/health` responds

<!-- HUB-MCP-CHANGE-REQUESTS -->
## Hub MCP — filing change requests (hub-side fixes)

You are the AI agent working inside this storefront's repo. Edit THIS store's
files directly — that is your job.

> **🚫 NEVER update the hub directly.** The hub lives at `~/projects/hub/`
> (and its production equivalents). You must not edit, commit, push, or run
> management commands against the hub repo, the hub database, or the hub's
> services — and never try to "fix" the hub by writing to it. The ONLY
> sanctioned channel for hub changes is a change request (below), which the
> hub's human admin approves before anything happens.

### 1. Get your hub MCP key

Every store is provisioned with an AI-developer key (role `ai_developer`) on
the hub. Legacy stores like this one: ask the hub admin (or the user) to mint
one at **/hub/admin/agent-keys** (sidebar: Admin → Agent API Keys) with:

- **Label:** `advance store IDE agent`
- **Role:** `ai_developer`
- **Owner user:** the store's hub owner

Then add it to this repo's gitignored `.env` (perms 600):

    STORE_AI_DEVELOPER_API_KEY=<minted key>

A key is shown exactly once at mint time and can never be recovered (only
sha256 hashes are stored) — if it is lost or revoked, a new one must be
minted. Env-var presence alone grants nothing: the key VALUE must match an
ACTIVE registered row, and its role must be active in the role catalogue.

### 2. Present the key per call

The hub MCP gateway is streamable HTTP at `http://ubuntu:5001/mcp`
(`http://<hub-host>:5001/mcp` in the cloud). It is stateless — no login, no
session. Present the key on **every call** as the `api_key` argument or an
`Authorization: Bearer <key>` header.

### 3. File a change request

Use the `change_request_submit` tool. ANY authenticated agent role may submit
(change_request_submit and support_ticket_submit are *ALL_ROLES tools), so
your `ai_developer` key is sufficient:

    change_request_submit(
        summary="Short problem (<300 chars)",
        description="Your full requested change",
        priority="medium",            # low | medium | high | critical
        user_name="<your display name>",
        api_key="<STORE_AI_DEVELOPER_API_KEY value>",
    )

- The ticket gets a number (#1, #2, ...) and appears on the admin's
  **Change Requests** page (/hub/changes).
- The admin records a recommended solution and approves/rejects with a
  written reason; the approved answer becomes the record for future agents.

For a user-facing problem ticket (subscription / shared-service
connectivity), use `support_ticket_submit` instead — it lands on the
Problem Tickets queue (/hub-tickets).

### Rules

- Edit THIS store's files directly — no ticket needed for store work.
- Use `change_request_submit` for changes TO THE HUB, not for this store.
- Never work around the system: file the ticket and wait for the decision.
- Never commit `.env` — it holds your key and the store's other secrets.

### Hub change requests — resolved

**Ticket #14** (`http://ubuntu:5000/hub/changes/14`, approved; store side
complete) — the exposed shared `ai_developer` key (agent_keys id=6, prefix
`L1VEQggw`) was revoked and advance was issued its **own per-store** key,
delivered into `.env` as `STORE_AI_DEVELOPER_API_KEY` (perms 600).

**Ticket #13** (`http://ubuntu:5000/hub/changes/13`, approved; store side
complete) — the hub now pushes hub-issued role keys into opt-in stores' `.env`
(dev + prod MicroVM) and re-pushes them on rotation. advance's `.env` carries
`HUB_MARKETING_API_KEY` and `HUB_SYSOP_API_KEY`.

> The earlier ticket **#12** (a store writing its own admin password into the
> hub vault) was **rejected** — the vault is for hub/shared-service credentials
> only. #13 is the inverse (hub issues, store consumes), which fits that
> design. Do not re-propose the #12 shape.

### Hub key model — two directions of trust

| Env var | Direction | Scope | Rotation |
|---------|-----------|-------|----------|
| `STORE_AI_DEVELOPER_API_KEY` | store → hub | **unique per store** | store's own IDE-agent identity |
| `HUB_MARKETING_API_KEY` | hub → store | **shared across the owner's stores** | hub mints/rotates; store consumes |
| `HUB_SYSOP_API_KEY` | hub → store | **shared across the owner's stores** | hub mints/rotates; store consumes |

- The store **never rotates** the hub-issued `HUB_*` keys — the hub injects and
  maintains them in `.env` and re-pushes on rotation. Do not edit them by hand.
- The store's OWN identity is `STORE_AI_DEVELOPER_API_KEY` (unique per store);
  it is what the store's IDE agent presents to file change requests.
- **Consumer:** `apps/hub_roles.py` — the canonical shared client (copied
  unchanged from `mall-services`, stdlib-only). It calls the hub's plain-JSON
  role bridge (`POST <HUB_URL>/hub/api/role-call`) and **never raises**:
  returns `{"ok": True, "result": ...}` or `{"ok": False, "error": ...}`.
  Use `hub_roles.marketing("<tool>")` / `hub_roles.sysop("<tool>")`.
- **Monitoring-only in prod:** the store role bridge **refuses irreversible
  actions** (e.g. `marketing_entry_send`) with a 403 — those are run by the hub
  Marketing Manager agent in dev, tested, then pushed to prod. Do not add
  write/send call paths to the store. Reversible writes remain permitted.
- Config in `core/settings.py`; documented in `.env.example`.

### Hub-role agent training (marketing, sysop)

The **authoritative runbook for each role is served live by the hub** — never
copied into this repo. Every role self-trains over MCP in one call:

    mcp_setup            # detects your role from the key you present and
                         # returns the role runbook + the training self-check
    role_runbook role=marketing|sysop|ai_developer

See **`HUB-AGENT-TRAINING.md`** for the store-side onboarding of advance's
marketing and sysop agents: which key each holds, how to self-train, the tool
families available, and the rules (the store consumes the marketing/sysop keys
for monitoring only; sends are run by the hub agent in dev then pushed to prod;
sysop routine duties vs. change requests).
