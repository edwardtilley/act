# advance (advance) — Store AI Agent Instructions

> **Canonical project instructions for EVERY AI coding agent that opens this
> repo** — opencode, freebuff, Claude Code, or anything else. One store = one
> development agent; this file + `SOUL.md` + `README.md` are its base documents.
> Managed by the hub agent-template system
> (`_bm_reference/agent_templates/store/`, version tracked in
> `.ai-template-state.json`). The sync tool never overwrites a customized copy —
> it writes `AGENTS.new.md` instead, so your local lessons are always kept.

You are the AI agent working inside this storefront's repo. Edit THIS store's
files directly — that is your job. When you need a change or clarification
**to the hub itself** (a missing capability, an unclear hub procedure, or a
fix you cannot apply from here), file a change request instead of guessing.

## Your hub MCP key (auto-minted at provision)

This store was provisioned with an AI-developer MCP key on the hub. It lives
in this repo's **gitignored** `.env` (perms 600):

    HUB_AI_DEVELOPER_API_KEY=<minted at provision>

Read it from `.env` and present it on every hub MCP call — as the `api_key`
argument or an `Authorization: Bearer <key>` header. If the line is missing or
the key was revoked, ask the hub admin to mint a replacement at
`/hub/admin/agent-keys` (role: ai_developer) and re-add it to `.env`.

## Filing a change request (hub MCP)

The hub MCP gateway is streamable HTTP at `http://<hub-host>:5001/mcp` (the
`mcp:hub` server on this machine). Use `change_request_submit`:

    change_request_submit(
        summary="Short problem (<300 chars)",
        description="Your full requested change",
        priority="medium",            # low | medium | high | critical
        user_name="<your display name>",
        api_key="<HUB_AI_DEVELOPER_API_KEY value>",
    )

- ANY authenticated agent role may submit — your ai_developer key qualifies.
- The ticket gets a number (#1, #2, ...) and appears on the admin's **Change
  Requests** page (/hub/changes). The admin records a recommended solution and
  approves/rejects with a written reason; the approved answer becomes the
  record for future agents.
- For a user-facing problem ticket (subscription / shared-service
  connectivity), use `support_ticket_submit` instead — it lands on the
  Problem Tickets queue (/hub-tickets).

## Team roles visiting this store

The hub user's **Team** (Business Manager, Marketing Manager, System Operator,
Video Producer) acts through the hub MCP only — never by editing this repo.
If one of them appears here, point them at `mcp:hub role_runbook role=<role>`
and leave the code to this store's AI Developer.

## Rules

- Edit THIS store's files directly — no ticket needed for store work.
- Use `change_request_submit` for changes TO THE HUB, not for this store.
- Never work around the system: file the ticket and wait for the decision.
- Never commit `.env` — it holds your key and the store's other secrets.
- **Boot seeds initialize, never overwrite.** `ensure_default_user()` and any
  other seed helper may set a password/secret ONLY when creating the row —
  never re-apply it from `.env` on every boot. UI-managed state (e.g. a
  changed password) must stay the source of truth after first boot.
- **Never write test/verification rows to a live database.** Tests use a
  scratch database (temp-file SQLite) or a transaction that is rolled back,
  never committed. If a test "dodges" a uniqueness constraint with random
  suffixes, it is polluting the live DB — stop and switch to a scratch DB.
- **Snapshot before any restore.** Before overwriting ANY database file with
  a backup, copy the current file aside first
  (`cp db.sqlite3 db.pre-restore-$(date +%Y%m%d-%H%M%S).sqlite3`) so work
  created after the backup point is never silently destroyed.
- **The hub credential vault is for shared-service provider credentials only**
  (Stripe, Cloudflare, GitHub, email). Store-internal secrets (this app's
  admin login password, session keys) live in the store's own DB/`.env` —
  never file requests that push them into the hub vault.
