# Hub Architecture — Shared Services for All Stores

**Status:** ratified reference architecture.
**First deploy:** `advance` (party website = first store).
**Environments:** dev hub server (ubuntu) and production cloud servers.

All stores that connect to The Hub implement this architecture. The
per-store build procedure lives in `SOP-HUB-INTEGRATION.md`; this document
defines the architecture both environments operate to.

---

## 1. Components

```
                        ┌─────────────────────────────────────────┐
                        │            THE HUB (shared)             │
                        │  · Hub Payment Gateway  (HUB_GATEWAY_*) │
                        │  · Ops / automation (OpenClaw, Hermes)  │
                        │  · Financial consolidation              │
                        └──────────────┬──────────────────────────┘
                                       │ HTTPS
              ┌────────────────────────┼─────────────────────────┐
              │                        │                         │
       ┌──────▼────────┐      ┌────────▼────────┐      ┌────────▼────────┐
       │ advance store │      │ future store 2  │      │ future store 3  │
       │ (this repo)   │      │                 │      │                 │
       └──────┬────────┘      └─────────────────┘      └─────────────────┘
              ├─ UI pages          (cart / checkout / financial / health)
              ├─ REST API          (/api/v1/*, X-API-Key)
              └─ MCP tools         (/mcp/*, X-API-Key)
```

Every store exposes three surfaces, all backed by one shared service layer:

| Surface | Route | Consumer |
|---------|-------|----------|
| HTML pages | `/cart`, `/checkout`, `/orders`, `/financial`, `/health` | members & staff (browser) |
| REST API | `/api/v1/products|cart|checkout|orders|reports/financial|health` | hub machines, integrations |
| MCP tools | `/mcp/cart_status|checkout|financial_check|health_check` | OpenClaw / Hermes / human ops |

## 2. Contract rules (all stores, immutable)

1. **Money** — integer cents end to end; display formatting only in
   model properties/templates.
2. **Auth** — `X-API-Key` header; keys SHA-256-hashed in DB; roles
   `admin` (writes) and `sysop` (read-only). Env fallback:
   `API_KEY` (admin), `SYSOP_API_KEY` (sysop).
3. **Responses** — `{"success": true, "data": ...}` |
   `{"success": false, "error": "..."}`; ISO-8601 timestamps.
4. **Single source of truth** — one service layer per store
   (`apps/shop/store.py`) shared by UI, API, MCP (no duplicated queries).
5. **Health contract** — every store serves an identical health payload
   from the same builder (`services.service_health()`), at THREE endpoints:
   - `GET /api/v1/health` (sysop)
   - `GET /mcp/health_check` (sysop)
   - `GET /health` (staff browser page)
   The hub and its operations tools may query any of these; payloads match
   byte-for-byte so consolidation displays one status per store.
6. **Gateway contract** — charges POST to
   `HUB_GATEWAY_URL/v1/charges` with Bearer auth; success statuses
   `succeeded|paid|success|captured`; raw payloads archived in
   `Payment.raw_response`; hub failure never marks an order paid.

## 3. Environment configuration

| Env var | Dev (ubuntu hub) | Production (cloud) | Required |
|---------|------------------|--------------------|----------|
| `SECRET_KEY` | dev value | **new secret** | yes |
| `DEBUG` | `True` | `False` | yes |
| `ALLOWED_HOSTS` | `ubuntu,localhost,127.0.0.1,lan-ip` | cloud domain/IP | yes |
| `HUB_GATEWAY_URL` | *(unset → simulated)* | `https://gateway.hub.example` | prod |
| `HUB_GATEWAY_API_KEY` | *(unset → simulated)* | hub-issued secret | prod |
| `HUB_GATEWAY_SIMULATE` | `1` | `0` | prod |
| `API_KEY` / `SYSOP_API_KEY` | issue via `create_api_key` | same, new keys | both |

Simulation mode (`sim_` transaction ids) keeps the dev ubuntu server fully
functional before the hub's production gateway is reachable.

## 4. Deployment & operations

- **Dev hub server (ubuntu):** this repository, run via `env/bin/python
  manage.py runserver 0.0.0.0:5105` (or gunicorn) behind the local host;
  SQLite DB. Business manager and sysops check live status at
  `/health` (browser), `/mcp/health_check` or `/api/v1/health` (curl).
- **Production cloud:** gunicorn + multiple workers, `collectstatic` to
  `staticfiles/`, PostgreSQL-recommended (SQLite fine for small stores),
  secrets via environment/.env (never committed — see `.gitignore`),
  TLS termination at the load balancer, backups of the DB per store schedule.
- **Store versioning:** `services.VERSION` bumped per release and surfaced
  in every health payload; hub tracking consolidates store versions.

## 5. Status & reporting

| Event | Where it lands |
|-------|----------------|
| Charge attempted | `Payment` row + `raw_response` payload |
| Order paid | `Order.status=paid`, `Order.paid_at` |
| Revenue summary | `financial_report()` → `/financial`, `/api/v1/reports/financial`, `/mcp/financial_check` |
| Health snapshot | `service_health()` → `/health`, `/api/v1/health`, `/mcp/health_check` |
| Refunds | `Order→refunded`, `Payment→refunded` (hub egress) |

## 6. Per-store file map (reference: advance)

```
apps/shop/models.py      · services.py (keys, gateway, health)
apps/shop/store.py       · views_api.py · views_mcp.py · views_pages.py · urls.py
templates/shop/*.html    · SOP-HUB-INTEGRATION.md · HUB-ARCHITECTURE.md
```