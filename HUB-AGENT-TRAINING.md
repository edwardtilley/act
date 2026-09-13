# Hub Agent Training — advance

Onboarding + training for the **hub-role agents** that operate the `advance`
store — the **marketing** agent and the **sysop** agent. This is distinct from
the store's own IDE developer agent (see `AGENTS.md` / `SOUL.md`), which owns
the codebase.

The **authoritative, always-current runbook for each role is served live by the
hub** — it is never copied into this repo. This document tells each agent how to
fetch it and what to expect.

---

## 1. Two directions of trust (recap)

| Env var | Direction | Scope | Rotation |
|---------|-----------|-------|----------|
| `STORE_AI_DEVELOPER_API_KEY` | store → hub | **unique per store** | store's own IDE-agent identity |
| `HUB_MARKETING_API_KEY` | hub → store | **shared across the owner's stores** | hub mints/rotates; store consumes |
| `HUB_SYSOP_API_KEY` | hub → store | **shared across the owner's stores** | hub mints/rotates; store consumes |

- The store **never rotates** the `HUB_*` keys — the hub injects and maintains
  them in `.env` and re-pushes on rotation. Never edit them by hand.
- All three keys live in this repo's **gitignored** `.env` (perms 600).

---

## 2. One-call self-training (do this first, every role)

Every hub role trains itself over MCP with **`mcp_setup`** — no parameters.
The hub detects your role from the key you present and returns:

- your role name,
- the gateway + per-call auth facts,
- your role's **full runbook markdown**, and
- the **MCP Training Self-Check** assignment (run it and report the result).

- **Gateway:** `http://ubuntu:5001/mcp` (dev) — `http://<hub-host>:5001/mcp` in prod.
- **Auth:** present your key on every call as the `api_key` argument or an
  `Authorization: Bearer <key>` header. The gateway is stateless.

Training is an **agent** action, so call the MCP gateway directly with your key
(e.g. via your agent's MCP client). To fetch just the runbook, call
`role_runbook` with `role=marketing|sysop`.

> **Store-code** calls (the storefront calling hub shared services on a page)
> use the shared client **`apps/hub_roles.py`** instead — see §3/§4. That path
> goes through the hub's plain-JSON role bridge and is **monitoring-only**.

---

## 3. Marketing agent

**Key:** `HUB_MARKETING_API_KEY` (hub → store; shared; the store never rotates it).

**Self-train:** `mcp_setup` with the marketing key, then run its self-check.

**Store-side (monitoring only)** — use the shared client `apps/hub_roles.py`:

```python
from apps import hub_roles

hub_roles.marketing("marketing_campaign_list")   # campaign status
hub_roles.marketing("marketing_unsent_list")     # unsent / gap report
```

Returns `{"ok": True, "result": ...}` or `{"ok": False, "error": ...}` — it
never raises.

**Monitoring-only in prod.** The store role bridge **refuses irreversible
actions** (e.g. `marketing_entry_send`) with a 403. Sends are performed by the
hub Marketing Manager **agent** over MCP in dev, tested, then pushed to prod.
Do **not** add write/send call paths to the store. Reversible writes remain
permitted, but the store's purpose is read/monitor:

- Read/monitor: `marketing_campaign_list`, `marketing_campaign_get`,
  `marketing_entry_list`, `marketing_contacts_list`, `marketing_unsent_list`,
  `marketing_email_render`, `marketing_sweep_sheets`.
- Refused from the store: `marketing_entry_send` (and any `send` action).

**Rules**

- Never edit this repo's code, templates, or `.env` to publish marketing.
- Do not rotate or hand-edit the key; the hub owns it.
- When `HUB_MARKETING_API_KEY` is unset, `hub_roles` returns
  `{"ok": False, "error": "no marketing role key configured …"}`.

---

## 4. SysOp agent

**Key:** `HUB_SYSOP_API_KEY` (hub → store; shared; the store never rotates it).

**Self-train:** `mcp_setup` with the sysop key, then run its self-check.

**Store-side** — shared client `apps/hub_roles.py`:

```python
from apps import hub_roles
hub_roles.sysop("health_check")                  # store health
```

**What you can do** (hub sysop duties — details in the live runbook):

- Health / diagnostics: `health_check`, `tail_logs`, `view_logs`,
  `sysop_health_report`
- Restore / restart: `restart_app`, `run_command` (routine restore commands
  need no change request)
- Backups: `backup_database`, `github_backup`, `offbox_backup`,
  `store_data_backup`, `db_backup_library_run` / `_list` / `_restore`
- Key hygiene: `api_key_audit`, `api_key_update`

**Rules**

- Restoring a down store to green, the nightly GitHub push, the DB backup
  library run, key rotation, and health/backup reporting are **routine** (no
  change request).
- Any change to code/config/deps/data semantics still requires a
  `change_request_submit` + human approval.

---

## 5. Where the authority lives

- Live role runbooks + self-checks: hub `mcp_setup` / `role_runbook` (MCP gateway).
- Store-side consumer (monitoring): `apps/hub_roles.py` (hub role bridge).
- Key model + store policy: `AGENTS.md` §11.
- Config: `core/settings.py`; documented in `.env.example`.
