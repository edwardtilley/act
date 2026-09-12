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

Store-side, call it with the helper:

```python
from apps import hub_mcp
hub_mcp.call_tool('mcp_setup', role='marketing')   # or role='sysop'
```

You can also fetch just the runbook with
`hub_mcp.call_tool('role_runbook', {'role': 'marketing'}, role='marketing')`.

---

## 3. Marketing agent

**Key:** `HUB_MARKETING_API_KEY` (hub → store; shared; the store never rotates it).

**Self-train:** `mcp_setup` with the marketing key, then run its self-check.

**What you can do** (hub marketing tool families — details in the live runbook):

- Campaigns: `marketing_campaign_create` / `_update` / `_list` / `_get`
- Entries: `marketing_entry_add` / `_list` / `_update` / `_approve` / `_send`
- Contacts: `marketing_contact_upsert`, `marketing_contacts_list`
- Email: `marketing_email_render`, `marketing_unsent_list`, `marketing_unsent_revalidate`
- Sheets: `marketing_sweep_sheets`
- Affiliates / newsletter: `affiliate_network_*`, `affiliate_account_*`, `newsletter_subscribe`

**How (store-side)** — use the wrappers in `apps/hub_mcp.py`:

```python
from apps import hub_mcp
if hub_mcp.marketing_enabled():
    hub_mcp.marketing_campaign_list()
    hub_mcp.marketing_entry_list()
    hub_mcp.marketing_sweep_sheets(dry_run=True)
```

**Rules**

- Publish marketing content **via hub MCP tools only** — never edit this repo's
  code, templates, or `.env`.
- Do not rotate or hand-edit the key; the hub owns it.
- `hub_mcp.marketing_enabled()` is `True` only when the store is opted in
  (`HUB_MARKETING_API_KEY` set). When it is unset, calls raise `HubMCPError`.

---

## 4. SysOp agent

**Key:** `HUB_SYSOP_API_KEY` (hub → store; shared; the store never rotates it).

**Self-train:** `mcp_setup` with the sysop key, then run its self-check.

**What you can do** (hub sysop duties — details in the live runbook):

- Health / diagnostics: `health_check`, `tail_logs`, `view_logs`,
  `sysop_health_report`
- Restore / restart: `restart_app`, `run_command` (routine restore commands
  need no change request)
- Backups: `backup_database`, `github_backup`, `offbox_backup`,
  `store_data_backup`, `db_backup_library_run` / `_list` / `_restore`
- Key hygiene: `api_key_audit`, `api_key_update`

**How (store-side):**

```python
from apps import hub_mcp
hub_mcp.call_tool('health_check', role='sysop')
```

**Rules**

- Restoring a down store to green, the nightly GitHub push, the DB backup
  library run, key rotation, and health/backup reporting are **routine** (no
  change request).
- Any change to code/config/deps/data semantics still requires a
  `change_request_submit` + human approval.

---

## 5. Where the authority lives

- Live role runbooks + self-checks: hub `mcp_setup` / `role_runbook`.
- Key model + store policy: `AGENTS.md` §11.
- Store-side consumer: `apps/hub_mcp.py`.
- Config: `core/settings.py`; documented in `.env.example`.
