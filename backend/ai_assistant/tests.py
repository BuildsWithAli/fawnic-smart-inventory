"""
Tests for the agentic AI stock assistant's safety guarantees:

  1. The tool-call dispatcher (`agent._execute_tool`) only ever executes one of
     the four whitelisted functions — anything else is rejected before any code
     runs.
  2. flag_low_stock / suggest_reorder write real, ORM-fetched numbers into
     StockAlert — never a value invented by the caller.
  3. The full evaluate_order_stock() pipeline, driven by a scripted fake
     "model" that behaves like a real LLM would (reads stock, then decides),
     produces a StockAlert grounded in the actual Product row.
"""

from decimal import Decimal

from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import User
from inventory.models import Brand, Category, Product, Warehouse
from orders.models import Order, OrderItem
from partners.models import Customer

from .models import StockAlert
from .services import agent, tools
from .services.providers import AIProvider, ClaudeProvider, GeminiProvider, OllamaProvider, OpenAIProvider


def make_product(quantity, reorder_threshold, sku="FWN-TEST-001"):
    category, _ = Category.objects.get_or_create(name="Wallets")
    brand, _ = Brand.objects.get_or_create(name="FAWNIC Classic")
    warehouse, _ = Warehouse.objects.get_or_create(name="Main Warehouse")
    return Product.objects.create(
        sku=sku, name="Test Wallet", category=category, brand=brand, warehouse=warehouse,
        quantity=quantity, unit_cost=Decimal("10.00"), reorder_threshold=reorder_threshold,
    )


class ProviderSelectionTests(TestCase):
    """get_provider() must resolve to the configured provider, and fall back
    sensibly when the selected one has no key configured."""

    @override_settings(AI_PROVIDER="claude", ANTHROPIC_API_KEY="test-key")
    def test_selects_claude_when_configured(self):
        self.assertIsInstance(agent.get_provider(), ClaudeProvider)

    @override_settings(AI_PROVIDER="openai", OPENAI_API_KEY="test-key")
    def test_selects_openai_when_configured(self):
        self.assertIsInstance(agent.get_provider(), OpenAIProvider)

    @override_settings(AI_PROVIDER="gemini", GEMINI_API_KEY="test-key")
    def test_selects_gemini_when_configured(self):
        self.assertIsInstance(agent.get_provider(), GeminiProvider)

    @override_settings(
        AI_PROVIDER="gemini", GEMINI_API_KEY="", ANTHROPIC_API_KEY="", OPENAI_API_KEY="",
    )
    def test_falls_back_to_ollama_when_no_key_matches_selected_provider(self):
        self.assertIsInstance(agent.get_provider(), OllamaProvider)


class ToolWhitelistTests(TestCase):
    def test_only_four_tools_are_registered(self):
        self.assertEqual(
            set(agent.TOOL_FUNCTIONS.keys()),
            {"get_stock_level", "get_reorder_threshold", "flag_low_stock", "suggest_reorder"},
        )

    def test_unknown_tool_name_is_rejected_without_executing_anything(self):
        product = make_product(quantity=2, reorder_threshold=10)

        with self.assertRaises(LookupError):
            agent._execute_tool("delete_all_products", {"product_id": product.id})

        # Nothing should have changed: no alert created, product untouched.
        self.assertEqual(StockAlert.objects.count(), 0)
        product.refresh_from_db()
        self.assertEqual(product.quantity, 2)

    def test_execute_tool_dispatches_to_the_real_function(self):
        product = make_product(quantity=7, reorder_threshold=10)
        result = agent._execute_tool("get_stock_level", {"product_id": product.id})
        self.assertEqual(result["quantity"], 7)


class ToolFunctionTests(TestCase):
    def test_flag_low_stock_snapshots_real_numbers(self):
        product = make_product(quantity=3, reorder_threshold=10)
        customer = Customer.objects.create(name="Test Customer")
        order = Order.objects.create(customer=customer, status=Order.Status.CUTTING)

        result = tools.flag_low_stock(product_id=product.id, order_id=order.id, severity="high")

        alert = StockAlert.objects.get(pk=result["alert_id"])
        # The numbers on the alert must match what's actually in the Product row,
        # fetched independently here — not something the caller passed in.
        live_product = Product.objects.get(pk=product.id)
        self.assertEqual(alert.current_stock_at_alert, live_product.quantity)
        self.assertEqual(alert.reorder_threshold_at_alert, live_product.reorder_threshold)
        self.assertEqual(alert.severity, "high")
        self.assertEqual(alert.order_id, order.id)
        self.assertFalse(alert.resolved)

    def test_flag_low_stock_rejects_invalid_severity(self):
        product = make_product(quantity=3, reorder_threshold=10)
        with self.assertRaises(ValueError):
            tools.flag_low_stock(product_id=product.id, order_id=None, severity="catastrophic")

    def test_suggest_reorder_attaches_to_existing_alert(self):
        product = make_product(quantity=3, reorder_threshold=10)
        flagged = tools.flag_low_stock(product_id=product.id, order_id=None, severity="medium")

        result = tools.suggest_reorder(product_id=product.id, suggested_qty=25)

        alert = StockAlert.objects.get(pk=flagged["alert_id"])
        alert.refresh_from_db()
        self.assertEqual(alert.suggested_quantity, 25)
        self.assertEqual(result["alert_id"], alert.id)

    def test_suggest_reorder_rejects_non_positive_quantity(self):
        product = make_product(quantity=3, reorder_threshold=10)
        with self.assertRaises(ValueError):
            tools.suggest_reorder(product_id=product.id, suggested_qty=0)


class AlertRolePermissionTests(TestCase):
    """Support can view AI Alerts but must not resolve them; Owner and
    Inventory Manager can do both."""

    def setUp(self):
        product = make_product(quantity=2, reorder_threshold=10)
        result = tools.flag_low_stock(product_id=product.id, order_id=None, severity="high")
        self.alert = StockAlert.objects.get(pk=result["alert_id"])

        self.owner = User.objects.create_user(username="owner3", password="Test@12345", role=User.Role.OWNER)
        self.manager = User.objects.create_user(
            username="manager3", password="Test@12345", role=User.Role.INVENTORY_MANAGER
        )
        self.support = User.objects.create_user(username="support3", password="Test@12345", role=User.Role.SUPPORT)

    def _client_for(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_support_can_view_but_not_resolve(self):
        client = self._client_for(self.support)
        self.assertEqual(client.get("/api/alerts/").status_code, 200)
        self.assertEqual(client.post(f"/api/alerts/{self.alert.id}/resolve/").status_code, 403)
        self.alert.refresh_from_db()
        self.assertFalse(self.alert.resolved)

    def test_inventory_manager_can_resolve(self):
        client = self._client_for(self.manager)
        response = client.post(f"/api/alerts/{self.alert.id}/resolve/")
        self.assertEqual(response.status_code, 200)
        self.alert.refresh_from_db()
        self.assertTrue(self.alert.resolved)

    def test_owner_can_resolve(self):
        client = self._client_for(self.owner)
        response = client.post(f"/api/alerts/{self.alert.id}/resolve/")
        self.assertEqual(response.status_code, 200)


class ScriptedFakeProvider(AIProvider):
    """Stands in for a real LLM. Behaves the way a well-behaved model should:
    check real stock via tools, then decide whether to flag/suggest — it never
    invents a quantity itself. Also probes the whitelist with a disallowed tool
    name to prove the executor blocks it."""

    def run_tool_agent(self, *, system_prompt, user_prompt, tools, tool_executor, max_turns=6):
        calls = []

        # A hallucinated/out-of-scope tool call a real model might attempt —
        # must be rejected by the executor, not executed.
        try:
            tool_executor("update_product_quantity", {"product_id": 1, "quantity": 9999})
            calls.append(("update_product_quantity", "EXECUTED"))
        except LookupError:
            calls.append(("update_product_quantity", "REJECTED"))

        for product_id in self._product_ids:
            stock = tool_executor("get_stock_level", {"product_id": product_id})
            threshold = tool_executor("get_reorder_threshold", {"product_id": product_id})
            calls.append(("get_stock_level", stock))
            calls.append(("get_reorder_threshold", threshold))

            if stock["quantity"] <= threshold["reorder_threshold"]:
                severity = "critical" if stock["quantity"] == 0 else "high"
                alert = tool_executor(
                    "flag_low_stock",
                    {"product_id": product_id, "order_id": self._order_id, "severity": severity},
                )
                calls.append(("flag_low_stock", alert))
                suggestion = tool_executor(
                    "suggest_reorder",
                    {"product_id": product_id, "suggested_qty": threshold["reorder_threshold"] * 2},
                )
                calls.append(("suggest_reorder", suggestion))

        self.calls = calls
        return "done"

    def __init__(self, product_ids, order_id):
        self._product_ids = product_ids
        self._order_id = order_id


class EvaluateOrderStockTests(TransactionTestCase):
    """TransactionTestCase, not TestCase: evaluate_order_stock now runs the
    provider call in a worker thread (see agent.AI_CALL_TIMEOUT_SECONDS), which
    opens its own SQLite connection. TestCase's outer per-test transaction on
    the main connection would collide with that second connection's writes
    ("database is locked") — an artifact of the test wrapper, not of production
    request handling, where no such outer transaction is held open."""

    def test_low_stock_scenario_produces_alert_with_real_tool_retrieved_numbers(self):
        low_product = make_product(quantity=2, reorder_threshold=10, sku="FWN-LOW-001")
        healthy_product = make_product(quantity=100, reorder_threshold=10, sku="FWN-OK-001")
        customer = Customer.objects.create(name="Test Customer")
        order = Order.objects.create(customer=customer, status=Order.Status.CUTTING)
        OrderItem.objects.create(order=order, product=low_product, quantity=1)
        OrderItem.objects.create(order=order, product=healthy_product, quantity=1)

        fake_provider = ScriptedFakeProvider(product_ids=[low_product.id, healthy_product.id], order_id=order.id)

        original_get_chain = agent.get_provider_chain
        agent.get_provider_chain = lambda: [fake_provider]
        try:
            result = agent.evaluate_order_stock(order)
        finally:
            agent.get_provider_chain = original_get_chain

        self.assertEqual(result.status, "ok")

        # Exactly one alert, for the low-stock product only.
        alerts = StockAlert.objects.filter(order=order)
        self.assertEqual(alerts.count(), 1)
        alert = alerts.first()
        self.assertEqual(alert.product_id, low_product.id)

        # The numbers on the alert are the real, live Product numbers — proving
        # they came from get_stock_level/get_reorder_threshold, not invention.
        live_product = Product.objects.get(pk=low_product.id)
        self.assertEqual(alert.current_stock_at_alert, live_product.quantity)
        self.assertEqual(alert.current_stock_at_alert, 2)
        self.assertEqual(alert.reorder_threshold_at_alert, live_product.reorder_threshold)
        self.assertEqual(alert.suggested_quantity, 20)

        # The rogue tool call was rejected, not executed.
        rejected = [c for c in fake_provider.calls if c[0] == "update_product_quantity"]
        self.assertEqual(rejected, [("update_product_quantity", "REJECTED")])

        # Product.quantity was never touched by the agent pipeline.
        self.assertEqual(live_product.quantity, 2)

    def test_a_hanging_provider_does_not_block_beyond_the_timeout(self):
        """A provider whose run_tool_agent never returns (network hang, dead
        connection, etc.) must not be allowed to block the Kanban status-change
        request indefinitely — evaluate_order_stock has to give up and return."""
        import time

        class HangingProvider(AIProvider):
            def run_tool_agent(self, **kwargs):
                time.sleep(5)
                return "should never be reached in this test"

        product = make_product(quantity=2, reorder_threshold=10)
        customer = Customer.objects.create(name="Test Customer")
        order = Order.objects.create(customer=customer, status=Order.Status.CUTTING)
        OrderItem.objects.create(order=order, product=product, quantity=1)

        original_get_chain = agent.get_provider_chain
        original_timeout = agent.AI_CALL_TIMEOUT_SECONDS
        agent.get_provider_chain = lambda: [HangingProvider()]
        agent.AI_CALL_TIMEOUT_SECONDS = 0.2
        try:
            started = time.monotonic()
            result = agent.evaluate_order_stock(order)
            elapsed = time.monotonic() - started
        finally:
            agent.get_provider_chain = original_get_chain
            agent.AI_CALL_TIMEOUT_SECONDS = original_timeout

        self.assertEqual(result.status, "unavailable")
        self.assertLess(elapsed, 2, "evaluate_order_stock should give up at the timeout, not wait for the hang")
        # No alert was created either, since the (abandoned) call never got that far.
        self.assertEqual(StockAlert.objects.filter(order=order).count(), 0)

    def test_falls_back_to_next_rung_when_the_first_provider_errors(self):
        """A provider raising (e.g. a 429 rate-limit) must not drop the stock
        check — evaluate_order_stock advances to the next rung, which still
        produces the alert."""

        class ErroringProvider(AIProvider):
            model = "erroring-model"

            def run_tool_agent(self, **kwargs):
                raise RuntimeError("429 RESOURCE_EXHAUSTED (simulated)")

        low_product = make_product(quantity=1, reorder_threshold=10, sku="FWN-FB-001")
        customer = Customer.objects.create(name="Test Customer")
        order = Order.objects.create(customer=customer, status=Order.Status.CUTTING)
        OrderItem.objects.create(order=order, product=low_product, quantity=1)

        working = ScriptedFakeProvider(product_ids=[low_product.id], order_id=order.id)
        working.model = "working-model"

        original_get_chain = agent.get_provider_chain
        agent.get_provider_chain = lambda: [ErroringProvider(), working]
        try:
            result = agent.evaluate_order_stock(order)
        finally:
            agent.get_provider_chain = original_get_chain

        self.assertEqual(result.status, "ok")
        self.assertIn("working-model", result.provider)
        self.assertEqual(StockAlert.objects.filter(order=order, product=low_product).count(), 1)

    def test_result_is_unavailable_when_every_rung_fails(self):
        class ErroringProvider(AIProvider):
            def run_tool_agent(self, **kwargs):
                raise RuntimeError("provider down")

        product = make_product(quantity=1, reorder_threshold=10, sku="FWN-FB-002")
        customer = Customer.objects.create(name="Test Customer")
        order = Order.objects.create(customer=customer, status=Order.Status.CUTTING)
        OrderItem.objects.create(order=order, product=product, quantity=1)

        original_get_chain = agent.get_provider_chain
        agent.get_provider_chain = lambda: [ErroringProvider(), ErroringProvider()]
        try:
            result = agent.evaluate_order_stock(order)
        finally:
            agent.get_provider_chain = original_get_chain

        self.assertEqual(result.status, "unavailable")
        self.assertIsNone(result.provider)
        self.assertEqual(StockAlert.objects.filter(order=order).count(), 0)

    def test_result_is_skipped_when_the_order_has_no_line_items(self):
        customer = Customer.objects.create(name="Test Customer")
        order = Order.objects.create(customer=customer, status=Order.Status.CUTTING)

        # No provider should even be consulted.
        original_get_chain = agent.get_provider_chain
        agent.get_provider_chain = lambda: (_ for _ in ()).throw(AssertionError("should not be called"))
        try:
            result = agent.evaluate_order_stock(order)
        finally:
            agent.get_provider_chain = original_get_chain

        self.assertEqual(result.status, "skipped")


class ProviderChainTests(TestCase):
    """get_provider_chain() orders the configured provider first, adds the
    second Gemini model as its own rung, and always ends with Ollama."""

    @override_settings(
        AI_PROVIDER="gemini",
        GEMINI_API_KEY="test-key",
        GEMINI_MODEL="gemini-2.5-flash",
        GEMINI_FALLBACK_MODEL="gemini-2.5-flash-lite",
        ANTHROPIC_API_KEY="",
        OPENAI_API_KEY="",
    )
    def test_gemini_primary_then_gemini_fallback_then_ollama(self):
        chain = agent.get_provider_chain()
        self.assertEqual([type(p).__name__ for p in chain], ["GeminiProvider", "GeminiProvider", "OllamaProvider"])
        self.assertEqual(chain[0].model, "gemini-2.5-flash")
        self.assertEqual(chain[1].model, "gemini-2.5-flash-lite")

    @override_settings(
        AI_PROVIDER="gemini",
        GEMINI_API_KEY="test-key",
        GEMINI_MODEL="gemini-2.5-flash",
        GEMINI_FALLBACK_MODEL="gemini-2.5-flash",
    )
    def test_no_duplicate_gemini_rung_when_fallback_equals_primary(self):
        models = [p.model for p in agent.get_provider_chain() if type(p).__name__ == "GeminiProvider"]
        self.assertEqual(models, ["gemini-2.5-flash"])

    @override_settings(
        AI_PROVIDER="claude", ANTHROPIC_API_KEY="test-key", GEMINI_API_KEY="test-key", OPENAI_API_KEY="",
    )
    def test_configured_provider_leads_the_chain(self):
        chain = agent.get_provider_chain()
        self.assertEqual(type(chain[0]).__name__, "ClaudeProvider")
        self.assertEqual(type(chain[-1]).__name__, "OllamaProvider")
