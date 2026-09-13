# Advance — store-side tasks for CR #13 (hub role keys, monitoring-only)

**Reference:** hub Change Request #13 (recommended solution → FINAL section).
**Prerequisite:** the hub has already injected `HUB_MARKETING_API_KEY` and
`HUB_SYSOP_API_KEY` into this store's `.env` (perms 600). No key minting here.

## Context

advance already has `apps/hub_mcp.py` — a bespoke client that talks to the hub's
MCP gateway (`:5001`) and includes write/send wrappers. The hub has since
standardized the store-side consumer as a shared client that uses the hub's
plain-JSON role bridge, which the hub **enforces as monitoring-only**
(irreversible actions such as email send are refused server-side). Align advance
to that.

## Tasks

### 1. Add the canonical shared client (do NOT hand-write one)

```bash
cp ~/projects/mall-services/mall_services/services/hub_roles.py \
   ~/projects/advance/apps/hub_roles.py
```

It is stdlib-only and used unchanged. Do **not** add the `mall-services` pip pin
(this is a legacy store; copying the single file is the sanctioned path).

### 2. Update call sites to the shared client and REMOVE write/send paths

```python
from apps import hub_roles

hub_roles.marketing("marketing_campaign_list")   # campaign status
hub_roles.marketing("marketing_unsent_list")     # unsent / gap report
hub_roles.sysop("health_check")                  # store health
```

- Returns `{"ok": True, "result": ...}` or `{"ok": False, "error": ...}` — it
  never raises.
- **Delete the write + irreversible wrappers** from `apps/hub_mcp.py`:
  `marketing_entry_send`, `marketing_entry_approve`,
  `marketing_campaign_create`, `marketing_campaign_update`,
  `marketing_contact_upsert`.
- advance is **monitoring-only**: sends are performed by the hub Marketing
  Manager **agent** in dev, tested, then pushed to prod.
- Once nothing imports `apps/hub_mcp.py`, delete it (or leave it as a thin shim).

### 3. `core/settings.py` + `.env.example` — add (blank values)

```
HUB_URL=                 # blank -> falls back to HUB_CALLBACK_URL
HUB_MARKETING_API_KEY=
HUB_SYSOP_API_KEY=
```

`.env` already holds the real values, injected by the hub — **never commit `.env`**.

### 4. `advance/AGENTS.md` — document the key convention

`HUB_MARKETING_API_KEY` / `HUB_SYSOP_API_KEY` are **hub-issued** (hub → store),
**ONE value shared across all the owner's stores**, injected by the hub,
**monitoring-only in prod**, never rotated by the store. The store's OWN identity
key stays `STORE_AI_DEVELOPER_API_KEY` (**unique per store**).

## Verify

```python
from apps import hub_roles
hub_roles.marketing("marketing_campaign_list")            # -> {"ok": True, ...}
hub_roles.marketing("marketing_entry_send", entry_id=1)   # -> {"ok": False, ...} (403 refused)
```

- `python manage.py check` passes.
