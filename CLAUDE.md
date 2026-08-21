# FAWNIC — Smart Inventory & Order Management System
## Master Development Prompt for Claude Code

> **Usage note:** Save this file as `CLAUDE.md` in your project's root directory before starting Claude Code (not as a one-off chat message). Claude Code reads `CLAUDE.md` automatically at the start of every session, including after a resume — so if a session ends partway through this build (likely, given its size), you do not need to re-paste this document. Just say "continue" and it re-grounds itself from this file plus the current repo state.

You are a senior full-stack software engineer, Django architect, React engineer, UI/UX designer, database designer, and AI integration engineer.

Your task is to **build a complete, professional, production-quality Inventory & Order Management System for FAWNIC** based on the requirements below.

This is not a simple CRUD demo and must NOT look like Django Admin.

---

# 1. PROJECT OBJECTIVE

Build a modern web-based **Smart Inventory & Order Management System** for FAWNIC, a leather-goods business dealing with products such as wallets, belts, bags, leather materials, hardware, etc.

The system must provide:

- Professional inventory management
- Product/master-data management
- Supplier and customer management
- Purchase management
- Sales management
- Automatic stock adjustment
- Inventory analytics
- Custom order management
- Drag-and-drop production Kanban
- AI-powered stock checking
- Low-stock alerts
- Reorder suggestions
- Role-based authentication
- Responsive modern UI

The application should feel like a **real commercial SaaS product**, not a university CRUD project.

---

# 2. IMPORTANT UI/UX REQUIREMENT

## DO NOT USE DJANGO ADMIN AS THE FRONTEND

The dashboard and application interface must NOT resemble:

- Django Admin
- Django default admin templates
- Basic Bootstrap CRUD pages
- Plain HTML tables
- Generic CRUD generators
- Default React starter UI

Do not simply expose Django Admin.

Instead, build a completely custom frontend using:

- React
- Tailwind CSS
- Modern component architecture
- Professional SaaS-style layout
- Responsive design
- Cards
- Charts
- Data tables
- Modals/drawers
- Badges
- Dropdowns
- Search
- Filters
- Toast notifications
- Loading states
- Empty states
- Error states
- Confirmation dialogs

The visual quality should be comparable to a modern inventory/SaaS application.

Use **`lucide-react`** as the single icon library throughout the application. Do not mix multiple icon sets.

---

# 3. DESIGN DIRECTION

Create a premium, clean and modern **FAWNIC-branded** interface.

Design characteristics:

- Minimal but visually rich
- Professional
- Elegant
- Spacious
- Excellent typography
- Clear information hierarchy
- Subtle borders and shadows
- Consistent border radius
- Modern icons
- Smooth hover states
- Smooth transitions
- Responsive layouts
- Desktop-first but fully responsive

Use Tailwind CSS throughout the frontend.

Avoid excessive gradients, excessive animations, huge text, unnecessary decorative elements, and visually noisy layouts.

The interface should prioritize usability and business information.

---

# 4. APPLICATION LAYOUT

Create a persistent application shell containing:

## Sidebar

Include:

- FAWNIC logo/brand
- Dashboard
- Products
- Categories
- Brands
- Warehouses
- Stock
- Suppliers
- Customers
- Purchases
- Sales
- Orders / Kanban
- AI Alerts
- Settings

At the bottom:

- Current user profile
- User role
- Logout

The sidebar should support a collapsed state on desktop and a drawer/mobile state on smaller screens.

## Top Navigation

Include:

- Page title
- Breadcrumb where appropriate
- Global search
- Notification/alert icon
- User profile menu

---

# 5. DASHBOARD

The dashboard is one of the most important parts of the project.

It must be a **custom SaaS analytics dashboard**.

Do NOT make it look like Django Admin.

Do NOT simply display database tables.

Create a polished dashboard containing:

## KPI Cards

Display these live metrics:

1. Total Products
2. Low Stock
3. Out of Stock
4. Warehouses
5. Categories
6. Suppliers
7. Purchase Orders
8. Sales Orders
9. Monthly Revenue
10. Inventory Value

The values must come from live Django ORM aggregation/API data.

Each card should have:

- Appropriate icon
- Metric value
- Descriptive label
- Optional trend/change indicator where meaningful
- Professional visual hierarchy

---

# 6. DASHBOARD ANALYTICS

Add two major analytics sections.

## Sales vs Purchases Chart

Use Recharts.

Show the last 30 days.

Provide:

- Sales
- Purchases
- Date axis
- Tooltip
- Legend
- Responsive sizing

## Stock Health Chart

Use a donut/pie or equivalent professional visualization.

Show:

- In Stock
- Low Stock
- Out of Stock

Charts must use real API data.

Do not hardcode dashboard numbers.

---

# 7. DASHBOARD ADDITIONAL SECTIONS

Below the primary KPI/chart area, add useful business widgets such as:

### Recent Sales

Show recent sales with:

- Sale ID
- Customer
- Amount
- Date
- Status

### Recent Purchases

Show:

- Purchase ID
- Supplier
- Amount
- Date

### Low Stock Products

Show products approaching or below their reorder threshold.

Include:

- Product
- SKU
- Current quantity
- Reorder threshold
- Stock status

### Recent Orders

Show recent custom orders and their current production stage.

---

# 8. BACKEND ARCHITECTURE

Use:

- Python
- Django
- Django REST Framework
- Django ORM

Structure the backend cleanly.

Suggested Django apps:

- accounts
- inventory
- partners
- transactions
- orders
- ai_assistant
- dashboard

Keep business logic separate from views wherever practical.

Use serializers, viewsets/API views, services, permissions, validators, and reusable utilities appropriately.

---

# 9. DATABASE

Development database:

- SQLite

Design the project so that PostgreSQL can be used in production without major architectural changes.

Use proper:

- Primary keys
- Foreign keys
- Constraints
- Indexes where useful
- Decimal fields for monetary values
- Date/time fields
- Created/updated timestamps

Do not store calculated business metrics unnecessarily when they can be derived safely from source data.

---

# 10. DATA MODELS

Implement the following models.

## Product

Fields:

- SKU
- Name
- Category
- Brand
- Warehouse
- Quantity
- Unit cost
- Reorder threshold
- Created at
- Updated at

## Brand

- Name
- Description

## Category

- Name
- Description

## Warehouse

- Name
- Location
- Capacity notes

## Supplier

- Name
- Contact information
- Created/updated timestamps

## Customer

- Name
- Contact information
- Created/updated timestamps

## Purchase

- Supplier
- Date
- Total
- Line items

## PurchaseItem

- Purchase
- Product
- Quantity
- Unit cost

## Sale

- Customer
- Date
- Total
- Line items

## SaleItem

- Sale
- Product
- Quantity
- Unit price

## Order

Include:

- Order ID
- Customer
- Products
- Status
- Due date
- Created at
- Updated at

Order statuses:

1. Pending
2. Cutting
3. Stitching
4. Quality Check
5. Shipped

## StockAlert

Include:

- Product
- Related order
- Severity
- Suggested quantity
- Resolved
- Created timestamp

---

# 11. STOCK MANAGEMENT LOGIC

Stock must remain synchronized with transactions.

When a purchase is successfully created:

    Product quantity += purchased quantity

When a sale is successfully created:

    Product quantity -= sold quantity

Prevent sales from reducing inventory below the allowed quantity unless the business rule explicitly permits it.

Use database transactions where necessary.

Stock changes must be reliable and atomic.

Do not allow frontend-only stock manipulation.

The backend is the source of truth.

---

# 12. STOCK ADJUSTMENT AUDIT TRAIL

Implement stock adjustment functionality.

Each manual stock adjustment should record:

- Product
- Previous quantity
- New quantity
- Difference
- Adjustment reason
- User
- Timestamp

Provide a professional stock-history interface.

---

# 13. GENERIC CRUD ENGINE

A major architectural requirement is to avoid duplicating UI code for every CRUD module.

Create reusable React components such as:

- DataTable
- SearchBar
- FilterBar
- FormModal
- ConfirmDialog
- Pagination
- StatusBadge
- EmptyState
- LoadingState
- ErrorState

Use configuration-driven rendering where practical.

For example, different modules should be able to define:

- Columns
- Form fields
- Validation
- Filters
- API endpoint
- Actions

Then the shared CRUD engine can render the interface.

However, do NOT sacrifice usability or visual quality simply to make everything generic.

Specialized screens such as Dashboard and Kanban should have their own purpose-built UI.

---

# 14. PRODUCTS PAGE

Create a professional product-management screen.

Include:

- Search
- Category filter
- Brand filter
- Warehouse filter
- Stock-status filter
- Add Product
- Edit Product
- Delete Product
- View Product
- Pagination

Display useful columns such as:

- Product
- SKU
- Category
- Brand
- Warehouse
- Quantity
- Unit Cost
- Reorder Threshold
- Stock Status
- Actions

Use color-coded stock badges.

---

# 15. MASTER DATA MODULES

Build polished CRUD screens for:

- Products
- Brands
- Categories
- Warehouses
- Suppliers
- Customers

All must use the same design system.

Do not create six visually unrelated pages.

---

# 16. PURCHASE MANAGEMENT

Create purchase management UI.

Users should be able to:

- Create purchase
- Select supplier
- Add multiple products
- Enter quantities
- Enter unit costs
- Automatically calculate totals
- Review purchase before submission
- Save purchase

After successful creation, inventory must automatically increase.

Display purchase history in a professional table.

---

# 17. SALES MANAGEMENT

Create sales management UI.

Users should be able to:

- Create sale
- Select customer
- Add products
- Enter quantities
- Enter unit prices
- Automatically calculate totals
- Validate available stock
- Save sale

After successful creation, inventory must automatically decrease.

Display sales history.

---

# 18. KANBAN ORDER MANAGEMENT

Create a dedicated full-screen React Kanban interface.

Use:

    @hello-pangea/dnd

Columns:

- Pending
- Cutting
- Stitching
- Quality Check
- Shipped

Each order card should display:

- Order ID
- Customer
- Product(s)
- Due date
- Stock status
- AI alert indicator where applicable

Users should be able to drag cards between columns.

When a card moves:

    PATCH /api/orders/{id}/status/

Persist the new status in Django.

Show optimistic UI updates, but reconcile the result with the API response.

If the API fails:

- Roll back the card
- Show a visible error notification

---

# 19. AGENTIC AI STOCK ASSISTANT

Implement a controlled AI assistant using **tool/function calling**.

The AI must NOT have unrestricted database access.

The agent should activate when a Kanban order changes status.

The order's required materials and relevant stock information should be evaluated.

The AI should have only these tools:

    get_stock_level(product_id)

    get_reorder_threshold(product_id)

    flag_low_stock(product_id, order_id, severity)

    suggest_reorder(product_id, suggested_qty)

These tools must be implemented as real Django-side functions.

---

# 20. AI SAFETY RULES

This is extremely important.

The AI:

- Must never directly modify inventory tables.
- Must never invent stock quantities.
- Must never assume stock levels from memory.
- Must retrieve factual inventory information through tools.
- Must use structured/schema-constrained outputs.
- Must validate tool inputs and outputs server-side.
- Must only perform actions allowed by its predefined tools.

The AI's role is:

    Analyze → Check → Alert → Suggest

Not:

    Freely modify the database.

Persist AI-generated stock alerts in the StockAlert model.

---

# 21. AI ALERT UI

Create a dedicated Alerts panel/page.

Display:

- Product
- Related order
- Severity
- Current stock
- Reorder threshold
- Suggested reorder quantity
- Date
- Resolved status

Also show alert badges directly on Kanban cards.

Use clear severity indicators.

Allow users to mark alerts as resolved.

---

# 22. CLAUDE API

Use Anthropic Claude API as the primary hosted AI provider.

Keep the AI integration isolated behind a service layer.

For example:

    ai_assistant/services/claude_agent.py

The rest of the application should not depend directly on Anthropic SDK implementation details.

Environment variable:

    ANTHROPIC_API_KEY

Never hardcode API keys.

Use `.env`.

---

# 23. OPENAI FALLBACK

Design the AI service layer so OpenAI can be used as a fallback provider.

Use an abstraction such as:

    AIProvider

with implementations such as:

    ClaudeProvider
    OpenAIProvider

Do not tightly couple the application to one provider.

---

# 24. LOCAL AI

Add optional development support for:

- Ollama
- Llama 3

This should be treated as an optional dev-time/offline provider.

It must not prevent the application from working when Ollama is unavailable.

---

## ⛔ MANDATORY CHECKPOINT — DO NOT SKIP

After Sections 19–24 (the full agentic AI stock assistant) are implemented and wired to the Kanban status-change trigger, **stop before continuing to Section 25 onward.**

Produce a summary that explicitly states:

- Exactly which of the four tools were wired, and where each is implemented in the codebase.
- Proof the agent cannot call anything other than those four tools (show the tool-calling configuration).
- How you verified the agent never writes to `Product` or `StockAlert` outside of the `flag_low_stock`/`suggest_reorder` tool functions.
- At least one test case you ran (or wrote) showing a low-stock scenario correctly produces a `StockAlert` with real, tool-retrieved numbers — not invented ones.

Wait for explicit confirmation before proceeding. This is the single highest-risk part of the build and must be human-reviewed before more code is layered on top of it.

---

# 25. AUTHENTICATION

Use Django authentication, exposed to the React frontend via **JWT (`djangorestframework-simplejwt`)** — access + refresh tokens. Do not use Django's cookie-session auth for the API itself; reserve Django's session mechanism only for the Django Admin, which is not part of the user-facing application.

Support these roles:

- Owner
- Inventory Manager
- Support

At minimum, implement role-aware access at the application/authentication level.

Keep the architecture ready for more granular permissions later.

---

# 26. API DESIGN

Create clean REST APIs.

Example endpoints:

    /api/products/
    /api/brands/
    /api/categories/
    /api/warehouses/
    /api/suppliers/
    /api/customers/
    /api/purchases/
    /api/sales/
    /api/orders/
    /api/orders/{id}/status/
    /api/stock/
    /api/alerts/
    /api/dashboard/

Use proper HTTP methods and status codes.

Add validation and meaningful error responses.

---

# 27. DASHBOARD API

Create a dedicated dashboard endpoint that returns all required dashboard data.

It should provide:

- KPI values
- Sales vs purchase chart data
- Stock health data
- Recent sales
- Recent purchases
- Low-stock products
- Recent orders

Use Django ORM:

- Count
- Sum
- annotate
- aggregation
- filtering

Do not create a separate analytics database.

---

# 28. FRONTEND ARCHITECTURE

Use React with Vite, written in **TypeScript** (`.tsx`/`.ts`) throughout — not plain JavaScript. This matters most for the generic CRUD engine's per-model config objects, which should be strongly typed.

Recommended structure:

    frontend/
      src/
        components/
        layouts/
        pages/
        features/
        hooks/
        services/
        api/
        utils/
        types/
        routes/

Use reusable components and feature-based organization where appropriate.

---

# 29. DESIGN SYSTEM

Create reusable design primitives for:

- Buttons
- Inputs
- Selects
- Tables
- Cards
- Modals
- Badges
- Dropdowns
- Tooltips
- Toasts
- Tabs
- Pagination
- Skeleton loaders

Maintain consistent:

- Typography
- Spacing
- Border radius
- Shadows
- Icon sizes
- Form styling
- Table styling

---

# 30. RESPONSIVENESS

The application must work properly on:

- Desktop
- Laptop
- Tablet
- Mobile

Do not allow:

- Broken tables
- Horizontal overflow where avoidable
- Overlapping cards
- Broken sidebar
- Unusable forms

For complex tables on mobile, use appropriate responsive layouts.

---

# 31. UX DETAILS

Implement professional states:

### Loading
Use skeleton loaders or appropriate loading indicators.

### Empty
Explain what the user can do next.

Example:

    "No products found"
    "Add your first product to start managing inventory."

### Error
Show human-readable errors.

### Success
Use toast notifications.

### Delete
Always ask for confirmation before destructive operations.

### Forms
Validate fields and show errors near the relevant fields.

---

# 32. BRANDING

Use the FAWNIC brand throughout the application.

Application title:

    FAWNIC Smart Inventory

Use the FAWNIC identity consistently across:

- Login
- Sidebar
- Dashboard
- Page headers
- Browser title
- Empty states where appropriate

Do not create a generic "Django Inventory System" appearance.

---

# 33. LOGIN PAGE

Create a custom professional login page.

Do NOT use Django's default login page.

The login page should match the application's design system.

Include:

- FAWNIC branding
- Email/username
- Password
- Remember me if appropriate
- Login button
- Error handling

---

# 34. SETTINGS

Create a basic settings page containing appropriate application/user settings.

Do not implement features explicitly marked out of scope unless required for the core system.

---

# 35. OUT-OF-SCOPE FEATURES

Do NOT spend development time implementing these unless necessary for architecture:

- Multi-warehouse stock transfers
- Cross-warehouse logistics
- Fine-grained per-module permissions
- Email/SMS alerts
- Supplier performance scorecards
- Advanced procurement analytics
- Custom report builder
- Public customer order tracking portal

Keep these as future-ready architecture only.

---

# 36. DEVELOPMENT QUALITY

Follow professional engineering practices.

Requirements:

- Clean code
- DRY principles
- Reusable components
- Meaningful naming
- Type-safe frontend code (TypeScript, per Section 28)
- Environment variables
- Proper error handling
- API validation
- Database transactions
- Security-conscious implementation
- No hardcoded secrets
- No unnecessary duplication

---

# 37. TESTING

Add tests for important backend logic.

At minimum test:

- Product creation
- Purchase stock increase
- Sale stock decrease
- Insufficient stock validation
- Dashboard calculations
- Order status changes
- Stock-alert creation
- AI tool validation

Also manually verify all major frontend workflows.

---

# 38. SEED DATA

Create realistic demo/seed data for FAWNIC.

Include sample:

- Products
- Categories
- Brands
- Warehouses
- Suppliers
- Customers
- Purchases
- Sales
- Orders

Use realistic leather-goods examples such as:

- Leather Wallet
- Bifold Wallet
- Card Holder
- Leather Belt
- Leather Bag
- Buckle
- Leather Hide
- Thread
- Lining Material

Do not use meaningless dummy data such as:

    Product 1
    Product 2
    Test User

The demo should look believable.

---

# 39. PROJECT SETUP

Create a clean repository structure.

Suggested:

    fawnic-inventory/
      backend/
      frontend/
      .env.example
      README.md
      .gitignore
      CLAUDE.md

Before writing any code, initialize a git repository at the project root (`git init`) and make an initial empty commit. This is required so every later stage has a rollback point.

The README must explain:

- Project overview
- Architecture
- Tech stack
- Setup
- Environment variables
- Database setup
- Running backend
- Running frontend
- Seed data
- AI configuration
- Testing
- Production considerations

---

# 40. IMPLEMENTATION STRATEGY

Do not attempt to generate the entire project blindly in one step.

Work incrementally.

First:

1. Inspect the existing repository.
2. Determine what already exists.
3. Create the architecture.
4. Set up Django backend.
5. Set up React frontend.
6. Configure Tailwind.
7. Implement database models.
8. Implement APIs.
9. Implement authentication.
10. Implement dashboard.
11. Implement reusable CRUD engine.
12. Implement purchases/sales.
13. Implement Kanban.
14. Implement AI tools.
15. Integrate Claude.
16. Add alerts. **← Mandatory checkpoint above applies after this step.**
17. Add testing.
18. Polish UI.
19. Run the application.
20. Fix errors.
21. Verify the complete end-to-end workflow.

**Commit to git after completing each numbered step above**, with a clear, descriptive commit message stating what was added (e.g. `"Add Product/Brand/Category models and DRF viewsets"`). This gives a rollback point at every stage and lets you (or a resumed session) see exactly what state the project was in when something breaks.

Do not overwrite existing working code unnecessarily.

Before making major architectural changes, inspect the existing implementation.

---

# 41. IMPORTANT CLAUDE CODE BEHAVIOR

When working on this project:

- Inspect files before editing them.
- Reuse existing code where appropriate.
- Do not create duplicate components.
- Do not leave TODO placeholders for core features.
- Do not fake API responses.
- Do not hardcode dashboard metrics.
- Do not hardcode stock values.
- Do not use mock data once real APIs are available.
- Do not expose Django Admin as the main application UI.
- Do not stop after creating backend models.
- Continue until frontend and backend are connected.
- Run tests and build commands.
- Fix errors instead of merely reporting them.
- Keep the application runnable after every major stage.
- Commit to git after each stage in Section 40.
- Honor the Mandatory Checkpoint after Section 19–24 (AI integration) without exception — this is the one point where you must stop and wait, even though the rest of this document asks you to keep going.
- If you hit a genuine ambiguity this document does not resolve (a design choice, a naming decision, an edge case), state your assumption explicitly in your next summary rather than silently deciding and moving on — so it can be corrected cheaply instead of discovered later.

---

# 42. DEFINITION OF DONE

The project is considered complete only when:

- Django backend runs successfully.
- React frontend runs successfully.
- Database migrations work.
- Authentication works.
- Dashboard loads real data.
- All required CRUD modules work.
- Purchases update inventory.
- Sales update inventory.
- Stock adjustments have an audit trail.
- Kanban drag-and-drop works.
- Order status persists.
- AI stock-check workflow works.
- AI alerts are persisted and displayed.
- Dashboard charts use real API data.
- Responsive UI works.
- Loading/error/empty states exist.
- Seed/demo data is available.
- Tests for core business logic pass.
- README contains complete setup instructions.
- No core functionality depends on Django Admin.

Most importantly:

**The final application must look and feel like a polished FAWNIC SaaS inventory product, NOT like a Django Admin panel.**

When asked to verify completion, go through this list item by item and report pass/fail for each — do not simply assert the project is done.
