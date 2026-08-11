# SOP — Connecting a New Store to the Hub's Shared Services

**Reference implementation:** `advance` (first store to integrate)
**Date:** 2026-08-09
**Scope:** shared services provided by The Hub to every store: **user cart /
checkout**, **admin financial reporting**, **hub payment gateway** — exposed
to operators/machines via a small **REST API** (`/api/v1`) and **MCP tool
endpoints** (`/mcp/*`).

Every future store must follow this procedure so the hub can manage all stores
uniformly through one interface (OpenClaw / Hermes / human admin).

---

## 1. Terminology

| Term | Meaning |
|------|---------|
| Hub | The shared-services platform that owns the payment gateway and ops tooling |
| Store | A consumer site (e.g. `advance`) connected to the hub |
| API key | Machine credential, `X-API-Key` header, roles `admin` / `sysop` |
| MCP | Machine-callable control-plane endpoints at `/mcp/<tool>` |
| cents | All money is transmitted as **integer cents**, never floats |

---

## 2. Step 1 — Create the store app (reference: `apps/shop`)

```bash
mkdir -p apps/shop/management/commands
```

Models (see `apps/shop/models.py`): `Product`, `Cart`, `CartItem`, `Order`,
`OrderItem`, `Payment`, `ApiKey`.

Money rules:
- prices stored in `*_cents` (`PositiveIntegerField`)
- display helpers (`$199.00`) are **properties on the model**
  (`price_display`, `total_display`, `subtotal_display`)
- never round in the template layer

Order lifecycle: `pending → paid | failed | refunded | cancelled`.
Payment lifecycle: `pending → succeeded | failed | refunded`.

## 3. Step 2 — Issue and validate API keys

- Management command (prints the key **once**):

```bash
python manage.py create_api_key <name> --role admin|sysop
```

- Keys are stored **SHA-256 hashed** (`services.hash_key`) — a DB leak
  exposes no working keys.
- Auth decorator: `@require_api_key(['admin'])` or `['sysop', 'admin']`
- Fallback env-var keys kept for backward compatibility:
  - `API_KEY` → admin
  - `SYSOP_API_KEY` → sysop

## 4. Step 3 — REST API surface (reference: `/api/v1`, `apps/shop/views_api.py`)

| Method | Endpoint | Role | Purpose |
|--------|----------|------|---------|
| GET | `/api/v1/products` | sysop | List sellable products with `price_cents` |
| GET | `/api/v1/cart?user_id=N` | sysop | Snapshot of a user's cart |
| POST | `/api/v1/cart/add` `{user_id, product_id, quantity}` | admin | Add product |
| POST | `/api/v1/cart/remove` `{user_id, item_id}` | admin | Remove item |
| POST | `/api/v1/cart/set-quantity` | admin | Update qty (0 deletes) |
| POST | `/api/v1/checkout` `{user_id, card_token?, hub_ref?, payment_method?}` | admin | Create order + charge |
| GET | `/api/v1/orders?user_id=&status=` | sysop | Order history |
| GET | `/api/v1/reports/financial` | admin | Revenue report (all stores) |
| GET | `/api/v1/health` | sysop | Row counts + version |

Conventions:
- auth header: `X-API-Key: adv_...`
- JSON body; responses `{"success": true, "data": {...}}` or
  `{"success": false, "error": "..."}`
- timestamps ISO-8601; money integer cents
- `user_id` passed by the hub operator (user-scoped shop)

## 5. Step 4 — Connect the payment gateway (hub)

`apps/shop/services.charge_via_hub()` is the only charge path. Configuration
via environment (`.env`):

```
HUB_GATEWAY_URL=http://hub.example.com/gateway
HUB_GATEWAY_API_KEY=secret
HUB_GATEWAY_SIMULATE=1        # 1 = local simulation when hub is unset
```

Charge payload sent by the hub: `POST <url>/v1/charges` with
`Authorization: Bearer <key>`, body:

```json
{
  "order_id": 12,
  "amount_cents": 19900,
  "currency": "CAD",
  "card_token": "...",   // optional
  "hub_ref": "...",      // optional operator reference
  "meta": {"source": "advance-party", "user_id": 3}
}
```

Expected response `{transaction_id, status}`; `status` in
`(succeeded|paid|success|captured)` maps to payment `succeeded`.
The store records the raw payload in `Payment.raw_response` (ledger/drill-down).

**Failure mode:** hub unreachable → raise `HubGatewayError` — the charge is
never silently marked paid; orders remain `pending/failed`.

## 6. Step 5 — Publish MCP tools (reference: `/mcp`, `apps/shop/views_mcp.py`)

One route per tool — control-plane for operators/machines:

| Tool | Method | Role | Purpose |
|------|--------|------|---------|
| `/mcp/health_check` | GET | sysop | Service health + row counts + gateway mode |
| `/mcp/cart_status?user_id=N` | GET | sysop | Read-only cart snapshot |
| `/mcp/financial_check` | GET | admin | Read-only revenue/orders report (same data as `/reports/financial`) |
| `/mcp/checkout` | POST | admin | Order + gateway charge (`{user_id, hub_ref?}`) |

Rules:
- read-only endpoints are sysop-accessible; mutations require admin
- same `X-API-Key` auth as the REST API
- always JSON `{"success":..., "data"/"error":...}`

## 7. Step 6 — Store UI (reference: `templates/shop/*`, `views_pages.py`)

Pages mirror the autoresume dashboard pattern (sidebar-enabled,
login-required): `/cart`, `/checkout`, `/orders`, `/financial`.

- `financial` renders `financial_report()` — the same single source of
  truth used by API + MCP (never duplicate the query in the template).
- Sidebar integration points (see `templates/includes/sidebar.html`):
  - user area: My Profile / Pricing / Cart / My Orders
  - admin area: Stats Editor / Financial Reports
- `/pricing` buttons POST to `/cart/add` with the `product_id` (via
  `apps/party_pages/views.pricing`).

## 8. Verification checklist (per store, before release)

1. `python manage.py check` clean
2. API key issues + authenticates (`create_api_key` then curl)
3. Anonymous UI routes redirect to `/auth/login/` (302)
4. Cart add/get/remove/qty round-trips via API AND UI
5. Checkout via simulated gateway → order `paid`, payment `succeeded`,
   transaction id recorded; cart emptied
6. Hub outage (`HUB_GATEWAY_URL` invalid) → checkout fails, no fake "paid"
7. `/financial` staff-only; non-staff → 302 `/dashboard`
8. `/mcp/health_check`, `cart_status`, `financial_check` return
   `{"success": true, ...}` 200 with keys
9. Float money never appears in payloads (all cents)

---

## 9. Reference implementation map (advance = first store)

```
apps/shop/models.py         → Product, Cart, CartItem, Order, OrderItem, Payment, ApiKey
apps/shop/services.py       → hash_key, key auth, money_display, JsonError, hub gateway charge
apps/shop/store.py          → cart/checkout/reporting shared service layer
apps/shop/views_api.py      → /api/v1 REST endpoints
apps/shop/views_mcp.py      → /mcp tools
apps/shop/views_pages.py    → /cart /checkout /orders /financial
apps/shop/urls.py           → api_patterns / mcp_patterns / page_patterns
templates/shop/cart.html|checkout.html|orders.html|financial.html
```

When a second store connects, copy the app structure above, keep the hub's
API/MCP conventions, and only edit the store-local toggles (products, pricing
for the side, theme).