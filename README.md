# FAWNIC Smart Inventory & Order Management System

A production-quality inventory, purchasing, sales, and production-order management system for **FAWNIC**, a leather-goods business (wallets, belts, bags, leather materials, hardware). Built as a custom SaaS-style application — not Django Admin, not a generic CRUD scaffold.

## 1. Project Overview

FAWNIC needed a system to manage:

- Product/master data (products, brands, categories, warehouses)
- Suppliers and customers
- Purchases and sales, with automatic, atomic stock synchronization
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

Business logic lives in Django `services.py` modules, not in views or serializers — e.g. `transactions/services.py` (`create_purchase`, `create_sale`) and `inventory/services.py` (`adjust_stock`) wrap stock mutations in atomic transactions. The frontend never mutates stock directly; it only calls these API endpoints.

### The AI agent's safety design

The agent (`backend/ai_assistant/services/agent.py`) is triggered from `orders/views.py` whenever an order's Kanban status changes (`PATCH /api/orders/{id}/status/`). It can call **exactly four** tools, implemented as real Django functions in `ai_assistant/services/tools.py`:

- `get_stock_level(product_id)`
- `get_reorder_threshold(product_id)`
- `flag_low_stock(product_id, order_id, severity)`
- `suggest_reorder(product_id, suggested_qty)`

`agent.TOOL_FUNCTIONS` is a hard-coded dict mapping exactly those four names to those four functions — the dispatcher (`_execute_tool`) rejects anything not in that dict before any code runs. The model never receives an ORM handle, SQL access, or any code-execution path; it only exchanges JSON tool-call requests/results with the provider layer. Writes to `StockAlert` happen only inside `flag_low_stock`/`suggest_reorder`, which validate their own inputs independent of what the model claims. `Product.quantity` is never written by anything in `ai_assistant`.

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
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts |
| `DATABASE_URL_ENGINE` | Leave unset for SQLite; set to `postgresql` + the `DATABASE_*` vars for Postgres |
| `CORS_ALLOWED_ORIGINS` | Frontend origin(s), e.g. `http://localhost:5173` |
| `AI_PROVIDER` | `claude` \| `openai` \| `gemini` \| `ollama` |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY` | Only the one matching `AI_PROVIDER` is required |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | Only used when `AI_PROVIDER=ollama` |

`frontend/.env`:

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Django API base, e.g. `http://127.0.0.1:8000/api` |

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

Set `AI_PROVIDER` to whichever provider you have a key for. The system prompt instructs the model to check real stock via `get_stock_level`/`get_reorder_threshold` before ever calling `flag_low_stock`/`suggest_reorder` — it is structurally incapable of calling anything else (see Architecture above). If no provider is configured/reachable, the Kanban status update still succeeds; the AI check fails silently into the server log rather than blocking the request.

### Testing

```bash
cd backend
python manage.py test
```

Covers: product creation, purchase stock increase, sale stock decrease (and atomic rollback on insufficient stock), stock-adjustment audit trail, dashboard ORM aggregation correctness, order status updates (including AI-failure resilience), the AI tool whitelist (rejecting any non-whitelisted tool call), and a full agentic-loop test proving a low-stock scenario produces a `StockAlert` populated with real, tool-retrieved numbers.

Frontend workflows (login, dashboard, all CRUD screens, purchases/sales, Kanban drag-and-drop, alerts, responsive/mobile layout) were manually verified in a real browser against the live backend.

### Production considerations

- Switch `DATABASE_URL_ENGINE=postgresql` and set the `DATABASE_*` vars — models use only Django-portable field types.
- Set a real `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, and a proper `DJANGO_ALLOWED_HOSTS`.
- Put `ai_assistant`'s external provider calls behind a task queue if request latency to Claude/OpenAI/Gemini becomes a concern (currently synchronous within the status-update request).
- Django Admin (`/admin/`) is available for superusers but is not part of, and not required by, the user-facing application.
