# FAWNIC Smart Inventory & Order Management System

A production-quality inventory, purchasing, sales, and production-order management system for **FAWNIC**, a leather-goods business (wallets, belts, bags, leather materials, hardware). Built as a custom SaaS-style application — not Django Admin, not a generic CRUD scaffold.

`django` `django-rest-framework` `react` `typescript` `vite` `tailwindcss` `inventory-management` `order-management` `kanban` `ai-agent` `claude` `sqlite`

**Live demo:** frontend <https://fawnic-smart-inventory.vercel.app> · API <https://fawnic-backend.onrender.com/api/>
Sign in with `owner` / `Owner@12345`. Both run on free tiers — the backend sleeps when idle, so the first request after a pause takes ~50s to wake.

## 1. Project Overview

FAWNIC needed a system to manage:

- Product/master data (products, brands, categories, warehouses)
- Suppliers and customers
- Purchases and sales, with automatic, atomic stock synchronization — deleting a purchase or sale reverses its stock effect in the same transaction (a purchase deletion is refused if that stock has since been sold)
- A manual stock-adjustment audit trail
- Custom production orders tracked through a drag-and-drop Kanban board (Pending → Cutting → Stitching → Quality Check → Shipped)
- An **agentic AI stock assistant** that checks real stock levels when an order's status changes and raises alerts / reorder suggestions — using tool-calling with a hard-coded, closed set of four tools, never direct database access
- A live analytics dashboard (KPIs, sales-vs-purchases trend, stock health, recent activity)
- Role-aware authentication (Owner, Inventory Manager, Support)

## 2. Architecture

```
fawnic-inventory/ (repo root)
├── backend/                 Django + DRF API (source of truth for all business logic)
│   ├── config/               settings, URL routing, pagination, exception handling
│   ├── accounts/              custom User model (role field), JWT auth endpoints
│   ├── inventory/              Product, Brand, Category, Warehouse, StockAdjustment
│   ├── partners/                Supplier, Customer
│   ├── transactions/             Purchase/PurchaseItem, Sale/SaleItem + stock-sync services
│   ├── orders/                    Order/OrderItem, Kanban status endpoint
│   ├── ai_assistant/                StockAlert model + the AI agent (tools/providers/agent)
│   └── dashboard/                    ORM-aggregated analytics endpoint
└── frontend/                 React + TypeScript + Vite + Tailwind CSS v4
    └── src/
        ├── components/ui/       design-system primitives (Button, Input, Modal, Badge, ...)
        ├── components/crud/      generic, config-driven CRUD engine (DataTable, FormModal, ...)
        ├── layouts/                app shell (collapsible/mobile sidebar, topbar)
        ├── pages/                   one screen per route
        ├── features/                 purpose-built UI for Kanban/alerts
        ├── services/ + api/            typed REST client, JWT refresh interceptor
        └── hooks/                       auth context, toast system, debounce
```

Business logic lives in Django `services.py` modules, not in views or serializers — e.g. `transactions/services.py` (`create_purchase`, `create_sale`, and their counterparts `delete_purchase`, `delete_sale`, which reverse the stock delta on deletion) and `inventory/services.py` (`adjust_stock`) wrap stock mutations in atomic transactions. The frontend never mutates stock directly; it only calls these API endpoints. Deleting a `Sale` that was auto-generated from a shipped order also rewinds that order to Quality Check so the Kanban board stays consistent.

**Shipped-column archiving.** An order records `shipped_at` the moment it transitions into Shipped (re-stamped if it leaves and returns). By default the Kanban board only fetches Shipped orders from the last 21 days — `GET /api/orders/?shipped_within_days=21`, a filter the board opts into; orders in every other column are never affected regardless of age or due date. Older Shipped orders are still one click away via the board's "Show all shipped orders" toggle, and nothing is deleted or hidden anywhere else — the Orders data, Sales history, and dashboard all ignore the parameter and see every order.

### The AI agent's safety design

The agent (`backend/ai_assistant/services/agent.py`) is triggered from `orders/views.py` whenever an order's Kanban status changes (`PATCH /api/orders/{id}/status/`). It can call **exactly four** tools, implemented as real Django functions in `ai_assistant/services/tools.py`:

- `get_stock_level(product_id)`
- `get_reorder_threshold(product_id)`
- `flag_low_stock(product_id, order_id, severity)`
- `suggest_reorder(product_id, suggested_qty)`

`agent.TOOL_FUNCTIONS` is a hard-coded dict mapping exactly those four names to those four functions — the dispatcher (`_execute_tool`) rejects anything not in that dict before any code runs. The model never receives an ORM handle, SQL access, or any code-execution path; it only exchanges JSON tool-call requests/results with the provider layer. Writes to `StockAlert` happen only inside `flag_low_stock`/`suggest_reorder`, which validate their own inputs independent of what the model claims. `Product.quantity` is never written by anything in `ai_assistant`.

`flag_low_stock` is idempotent per order: a repeat call for the same product+order refreshes the existing open alert instead of stacking a duplicate, backed by a partial unique constraint (`uniq_open_stockalert_per_product_order`). This absorbs the case where a timed-out provider rung's abandoned worker thread finishes after a later rung already flagged the same order.

The provider layer (`ai_assistant/services/providers.py`) implements a single `AIProvider` interface with `ClaudeProvider`, `OpenAIProvider`, `GeminiProvider`, and an optional local `OllamaProvider` — the rest of the app only ever talks to `AIProvider`, never to a specific SDK.

## 3. Tech Stack

- **Backend:** Python, Django 6, Django REST Framework, `djangorestframework-simplejwt`, `django-cors-headers`, `django-filter`, SQLite (dev) / PostgreSQL-ready
- **AI:** `anthropic`, `openai`, `google-genai` SDKs behind a provider abstraction; optional local Ollama
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS v4, `react-router-dom`, `recharts`, `@hello-pangea/dnd`, `lucide-react`, `axios`

## 4. Setup

### Prerequisites

- Python 3.11+ (a `py`/`python` launcher on PATH)
- Node.js 18+ and npm

### Clone & environment variables

Copy the example env files and fill in what you need:

```bash
cp .env.example backend/.env
cp frontend/.env.example frontend/.env
```

`backend/.env`:

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django secret key (set a real random value in production) |
| `DJANGO_DEBUG` | `True` for local dev |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts. Render's own `*.onrender.com` hostname is trusted automatically via `RENDER_EXTERNAL_HOSTNAME`, so it only needs a value for a custom domain |
| `DATABASE_URL` | A single Postgres connection URL (Render's managed-DB format). Takes precedence over everything below; leave unset for local SQLite |
| `DATABASE_URL_ENGINE` | Alternative to `DATABASE_URL`: set to `postgresql` + the discrete `DATABASE_*` vars |
| `CORS_ALLOWED_ORIGINS` | Frontend origin(s), e.g. `http://localhost:5173` |
| `AI_PROVIDER` | `claude` \| `openai` \| `gemini` \| `ollama` — the first rung of the stock-check fallback chain |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY` | The one matching `AI_PROVIDER` is required; any others set become extra fallback rungs |
| `ANTHROPIC_MODEL` / `OPENAI_MODEL` / `GEMINI_MODEL` | Model per provider. Defaults: `claude-sonnet-4-5-20250929`, `gpt-4o-mini`, `gemini-3.6-flash` |
| `GEMINI_FALLBACK_MODEL` | Second Gemini model tried if `GEMINI_MODEL` is rate-limited (default `gemini-3.5-flash-lite`) |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | Only used when `AI_PROVIDER=ollama` |

`frontend/.env`:

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Django API base, e.g. `http://127.0.0.1:8000/api` locally, or `https://<your-backend>/api` in production. Compiled into the bundle at build time — a rebuild is required after changing it |

### Database setup & running the backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate    macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser     # optional, for /admin/ (not part of the app UI)
python manage.py seed_data           # realistic FAWNIC demo data — see below

python manage.py runserver 8000
```

The API is now at `http://127.0.0.1:8000/api/`.

### Running the frontend

```bash
cd frontend
npm install
npm run dev
```

The app is now at `http://localhost:5173/`.

### Seed data

`python manage.py seed_data` (idempotent — safe to re-run) creates:

- 3 demo users: `owner` / `manager` / `support`, passwords `Owner@12345` / `Manager@12345` / `Support@12345`
- Realistic categories, brands, warehouses
- 15 leather-goods products (wallets, belts, bags, hides, thread, buckles, zippers...) with a mix of healthy, low, and out-of-stock quantities
- 3 suppliers, 4 customers
- Purchases and sales (via the real stock-sync service functions, so inventory numbers are internally consistent)
- 6 production orders spread across every Kanban column

### AI configuration

Set `AI_PROVIDER` to whichever provider you have a key for. The system prompt instructs the model to check real stock via `get_stock_level`/`get_reorder_threshold` before ever calling `flag_low_stock`/`suggest_reorder` — it is structurally incapable of calling anything else (see Architecture above).

**Fallback chain.** `evaluate_order_stock` tries providers in order: the configured `AI_PROVIDER` first, then (when Gemini is configured) `GEMINI_FALLBACK_MODEL`, then every other provider that has credentials, then local Ollama. If one rung errors or times out — e.g. a Gemini free-tier `429 RESOURCE_EXHAUSTED` (free-tier RPD is small; `gemini-3.6-flash` is ~20/day, `-flash-lite` variants are higher — check <https://aistudio.google.com/rate-limit> for your project's real ceiling) — the next rung gets a turn. Rungs share a 45-second overall budget and a 25-second per-rung cap, so neither a slow rung nor the whole chain can stall the Kanban request.

**Visibility.** The Kanban status update always succeeds regardless of the AI outcome. `PATCH /api/orders/{id}/status/` returns an `ai_stock_check` field — `"ok"` (a provider ran the check), `"skipped"` (order has no line items), or `"unavailable"` (every rung failed). The board toasts on `"unavailable"` and refreshes the alert bell so a rate-limit is visible instead of silent.

### Testing

```bash
cd backend
python manage.py test
```

Covers: product creation, purchase stock increase, sale stock decrease (and atomic rollback on insufficient stock), stock reversal when a purchase or sale is deleted (including the block when a purchase's stock was already sold, role-permission enforcement on delete, and the order rewind for an auto-generated sale), stock-adjustment audit trail, dashboard ORM aggregation correctness, order status updates (including AI-failure resilience), `shipped_at` stamping and the Shipped-column window filter (old shipped orders excluded by default, non-Shipped orders never affected), the AI tool whitelist (rejecting any non-whitelisted tool call), and a full agentic-loop test proving a low-stock scenario produces a `StockAlert` populated with real, tool-retrieved numbers.

Frontend workflows (login, dashboard, all CRUD screens, purchases/sales, Kanban drag-and-drop, alerts, responsive/mobile layout) were manually verified in a real browser against the live backend.

### Deployment (free tier)

The repo is wired for a zero-cost demo deploy: **Render** for the Django API + Postgres, **Vercel** for the React frontend.

**Backend — Render.** `render.yaml` at the repo root is a Blueprint: it provisions a free Postgres DB (`fawnic-db`) and a free Python web service (`fawnic-backend`), runs `migrate` → `seed_data` → `collectstatic` in the build, and starts `gunicorn`. `DJANGO_SECRET_KEY` is generated; `DATABASE_URL` is wired from the DB. Set the remaining secrets in the Render dashboard (they are `sync: false` in the file, never committed): `CORS_ALLOWED_ORIGINS` (your Vercel origin, no trailing slash), `AI_PROVIDER`, and the matching `*_API_KEY`.
Deploy: Render → **New → Blueprint** → pick this repo. `seed_data` runs in the build because the free tier has no shell — that is what puts the demo logins in the deployed DB. The free instance sleeps after ~15 min idle (~50s cold start) and the free Postgres expires after ~30 days.

**Frontend — Vercel.** Import the repo, set **Root Directory** to `frontend` (framework auto-detects as Vite). Add one env var, `VITE_API_BASE_URL` = `https://<your-render-service>.onrender.com/api`, as a plain **Config** value — not "Secret", since `VITE_`-prefixed vars are compiled into the public bundle. `frontend/vercel.json` handles the SPA rewrite so React Router deep links don't 404. Changing the env var needs a redeploy to take effect.

After both are up, make sure Render's `CORS_ALLOWED_ORIGINS` contains the final Vercel URL.

### Other production considerations

- For a non-Render Postgres, set `DATABASE_URL` (or `DATABASE_URL_ENGINE=postgresql` + the discrete `DATABASE_*` vars) — models use only Django-portable field types.
- Outside Render, set a real `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, and a proper `DJANGO_ALLOWED_HOSTS`.
- Put `ai_assistant`'s external provider calls behind a task queue if request latency to Claude/OpenAI/Gemini becomes a concern (currently synchronous within the status-update request, bounded by a shared 45s timeout across fallback rungs).
- Django Admin (`/admin/`) is available for superusers but is not part of, and not required by, the user-facing application.
