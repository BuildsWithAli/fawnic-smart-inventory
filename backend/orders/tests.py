from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from ai_assistant.models import StockAlert
from inventory.models import Brand, Category, Product, Warehouse
from partners.models import Customer
from transactions.models import Sale

from .models import Order, OrderItem


class OrderStatusUpdateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="Test@12345", role=User.Role.OWNER)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        category = Category.objects.create(name="Wallets")
        brand = Brand.objects.create(name="FAWNIC Classic")
        warehouse = Warehouse.objects.create(name="Main Warehouse")
        self.product = Product.objects.create(
            sku="FWN-TEST-001", name="Test Wallet", category=category, brand=brand,
            warehouse=warehouse, quantity=3, unit_cost=Decimal("10.00"), reorder_threshold=10,
        )
        self.customer = Customer.objects.create(name="Test Customer")
        self.order = Order.objects.create(customer=self.customer, status=Order.Status.PENDING)
        OrderItem.objects.create(order=self.order, product=self.product, quantity=2)

    @patch("ai_assistant.services.agent.evaluate_order_stock")
    def test_status_update_persists_and_triggers_ai_check(self, mock_evaluate):
        from ai_assistant.services.agent import StockCheckResult

        mock_evaluate.return_value = StockCheckResult(status="ok", summary="looks fine", provider="TestProvider")

        response = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "cutting"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["ai_stock_check"], "ok")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "cutting")
        mock_evaluate.assert_called_once_with(self.order)

    @patch("ai_assistant.services.agent.evaluate_order_stock", side_effect=RuntimeError("provider down"))
    def test_status_update_succeeds_even_if_ai_check_fails(self, mock_evaluate):
        response = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "cutting"}, format="json")

        self.assertEqual(response.status_code, 200)
        # The status change is saved, and the response says the check didn't run
        # (rather than silently implying stock is fine).
        self.assertEqual(response.data["ai_stock_check"], "unavailable")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "cutting")

    @patch("ai_assistant.services.agent.evaluate_order_stock")
    def test_status_update_reports_ai_check_unavailable_when_all_providers_fail(self, mock_evaluate):
        from ai_assistant.services.agent import StockCheckResult

        mock_evaluate.return_value = StockCheckResult(status="unavailable", summary=None, provider=None)

        response = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "cutting"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["ai_stock_check"], "unavailable")


@patch("ai_assistant.services.agent.evaluate_order_stock")
class ShippedTriggersSaleTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester2", password="Test@12345", role=User.Role.OWNER)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        category = Category.objects.create(name="Wallets")
        brand = Brand.objects.create(name="FAWNIC Classic")
        warehouse = Warehouse.objects.create(name="Main Warehouse")
        self.product_a = Product.objects.create(
            sku="FWN-TEST-A", name="Test Wallet A", category=category, brand=brand,
            warehouse=warehouse, quantity=10, unit_cost=Decimal("10.00"), reorder_threshold=2,
        )
        self.product_b = Product.objects.create(
            sku="FWN-TEST-B", name="Test Wallet B", category=category, brand=brand,
            warehouse=warehouse, quantity=5, unit_cost=Decimal("8.00"), reorder_threshold=2,
        )
        self.customer = Customer.objects.create(name="Test Customer")
        self.order = Order.objects.create(customer=self.customer, status=Order.Status.QUALITY_CHECK)
        OrderItem.objects.create(order=self.order, product=self.product_a, quantity=3, unit_price=Decimal("25.00"))
        OrderItem.objects.create(order=self.order, product=self.product_b, quantity=2, unit_price=Decimal("15.00"))

    def test_shipping_order_creates_sale_with_customer_and_items(self, mock_evaluate):
        response = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "shipped"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Sale.objects.count(), 1)

        sale = Sale.objects.get()
        self.assertEqual(sale.customer, self.customer)
        self.assertEqual(sale.items.count(), 2)

        item_a = sale.items.get(product=self.product_a)
        self.assertEqual(item_a.quantity, 3)
        self.assertEqual(item_a.unit_price, Decimal("25.00"))
        item_b = sale.items.get(product=self.product_b)
        self.assertEqual(item_b.quantity, 2)
        self.assertEqual(item_b.unit_price, Decimal("15.00"))

        self.order.refresh_from_db()
        self.assertEqual(self.order.generated_sale_id, sale.id)

        self.product_a.refresh_from_db()
        self.product_b.refresh_from_db()
        self.assertEqual(self.product_a.quantity, 7)
        self.assertEqual(self.product_b.quantity, 3)

    def test_shipping_twice_does_not_duplicate_sale(self, mock_evaluate):
        first = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "shipped"}, format="json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(Sale.objects.count(), 1)
        first_sale_id = Sale.objects.get().id

        back = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "cutting"}, format="json")
        self.assertEqual(back.status_code, 200)

        second = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "shipped"}, format="json")
        self.assertEqual(second.status_code, 200)

        self.assertEqual(Sale.objects.count(), 1)
        self.order.refresh_from_db()
        self.assertEqual(self.order.generated_sale_id, first_sale_id)

    def test_already_shipped_does_not_create_sale(self, mock_evaluate):
        self.order.status = Order.Status.SHIPPED
        self.order.save(update_fields=["status"])

        response = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "shipped"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Sale.objects.count(), 0)

    def test_insufficient_stock_blocks_transition_and_sale_creation(self, mock_evaluate):
        OrderItem.objects.create(order=self.order, product=self.product_b, quantity=999, unit_price=Decimal("15.00"))

        response = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "shipped"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Sale.objects.count(), 0)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.QUALITY_CHECK)
        self.assertIsNone(self.order.generated_sale_id)

        self.product_a.refresh_from_db()
        self.product_b.refresh_from_db()
        self.assertEqual(self.product_a.quantity, 10)
        self.assertEqual(self.product_b.quantity, 5)


class OrderDeleteTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner3", password="Test@12345", role=User.Role.OWNER)
        self.support = User.objects.create_user(username="support3", password="Test@12345", role=User.Role.SUPPORT)
        self.client = APIClient()

        category = Category.objects.create(name="Wallets")
        brand = Brand.objects.create(name="FAWNIC Classic")
        warehouse = Warehouse.objects.create(name="Main Warehouse")
        self.product = Product.objects.create(
            sku="FWN-TEST-DEL", name="Test Wallet", category=category, brand=brand,
            warehouse=warehouse, quantity=10, unit_cost=Decimal("10.00"), reorder_threshold=2,
        )
        self.customer = Customer.objects.create(name="Test Customer")

    def _order(self, status=Order.Status.PENDING):
        order = Order.objects.create(customer=self.customer, status=status)
        OrderItem.objects.create(order=order, product=self.product, quantity=1, unit_price=Decimal("20.00"))
        return order

    def test_owner_deletes_order_cleanly(self):
        order = self._order()
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(f"/api/orders/{order.id}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Order.objects.filter(pk=order.id).exists())

    def test_deleting_order_nulls_out_attached_alerts_instead_of_destroying_them(self):
        order = self._order()
        alert = StockAlert.objects.create(
            product=self.product,
            order=order,
            severity=StockAlert.Severity.HIGH,
            current_stock_at_alert=1,
            reorder_threshold_at_alert=2,
        )
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(f"/api/orders/{order.id}/")

        self.assertEqual(response.status_code, 204)
        alert.refresh_from_db()
        self.assertIsNone(alert.order_id)

    def test_cannot_delete_order_with_generated_sale(self):
        order = self._order(status=Order.Status.SHIPPED)
        sale = Sale.objects.create(customer=self.customer, date=timezone.now().date())
        order.generated_sale = sale
        order.save(update_fields=["generated_sale"])
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(f"/api/orders/{order.id}/")

        self.assertEqual(response.status_code, 400)
        self.assertTrue(Order.objects.filter(pk=order.id).exists())

    def test_support_cannot_delete_order(self):
        order = self._order()
        self.client.force_authenticate(user=self.support)

        response = self.client.delete(f"/api/orders/{order.id}/")

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Order.objects.filter(pk=order.id).exists())


@patch("ai_assistant.services.agent.evaluate_order_stock")
class ShippedAtTimestampTests(TestCase):
    """update_status stamps shipped_at on the transition into Shipped."""

    def setUp(self):
        self.user = User.objects.create_user(username="ship-ts", password="Test@12345", role=User.Role.OWNER)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        category = Category.objects.create(name="Wallets")
        brand = Brand.objects.create(name="FAWNIC Classic")
        warehouse = Warehouse.objects.create(name="Main Warehouse")
        self.product = Product.objects.create(
            sku="FWN-SHIP-TS", name="Test Wallet", category=category, brand=brand,
            warehouse=warehouse, quantity=50, unit_cost=Decimal("10.00"), reorder_threshold=2,
        )
        self.customer = Customer.objects.create(name="Test Customer")
        self.order = Order.objects.create(customer=self.customer, status=Order.Status.QUALITY_CHECK)
        OrderItem.objects.create(order=self.order, product=self.product, quantity=2, unit_price=Decimal("20.00"))

    def _mock_ok(self, mock_evaluate):
        from ai_assistant.services.agent import StockCheckResult

        mock_evaluate.return_value = StockCheckResult(status="ok", summary="fine", provider="TestProvider")

    def test_transition_into_shipped_sets_shipped_at(self, mock_evaluate):
        self._mock_ok(mock_evaluate)

        before = timezone.now()
        response = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "shipped"}, format="json")
        after = timezone.now()

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertIsNotNone(self.order.shipped_at)
        self.assertGreaterEqual(self.order.shipped_at, before)
        self.assertLessEqual(self.order.shipped_at, after)
        self.assertEqual(response.data["shipped_at"], self.order.shipped_at.isoformat().replace("+00:00", "Z"))

    def test_non_shipped_transition_leaves_shipped_at_null(self, mock_evaluate):
        self._mock_ok(mock_evaluate)

        response = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "cutting"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertIsNone(self.order.shipped_at)

    def test_reshipping_after_bounce_back_updates_shipped_at(self, mock_evaluate):
        self._mock_ok(mock_evaluate)

        self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "shipped"}, format="json")
        stale = timezone.now() - timedelta(days=5)
        Order.objects.filter(pk=self.order.pk).update(shipped_at=stale)

        self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "cutting"}, format="json")
        self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "shipped"}, format="json")

        self.order.refresh_from_db()
        self.assertGreater(self.order.shipped_at, stale)


class ShippedBoardWindowTests(TestCase):
    """`?shipped_within_days=N` trims only the Shipped column of the Kanban board fetch."""

    def setUp(self):
        self.user = User.objects.create_user(username="board-win", password="Test@12345", role=User.Role.OWNER)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        category = Category.objects.create(name="Wallets")
        brand = Brand.objects.create(name="FAWNIC Classic")
        warehouse = Warehouse.objects.create(name="Main Warehouse")
        self.product = Product.objects.create(
            sku="FWN-BOARD", name="Test Wallet", category=category, brand=brand,
            warehouse=warehouse, quantity=100, unit_cost=Decimal("10.00"), reorder_threshold=2,
        )
        self.customer = Customer.objects.create(name="Test Customer")

    def _order(self, status, shipped_at=None, due_date=None, age_days=None):
        order = Order.objects.create(customer=self.customer, status=status, due_date=due_date)
        OrderItem.objects.create(order=order, product=self.product, quantity=1, unit_price=Decimal("20.00"))
        updates = {}
        if shipped_at is not None:
            updates["shipped_at"] = shipped_at
        if age_days is not None:
            old = timezone.now() - timedelta(days=age_days)
            updates["created_at"] = old
            updates["updated_at"] = old
        if updates:
            Order.objects.filter(pk=order.pk).update(**updates)
        return order

    def _ids(self, response):
        self.assertEqual(response.status_code, 200)
        return {row["id"] for row in response.data["results"]}

    def test_old_shipped_order_excluded_from_windowed_fetch(self):
        old = self._order(Order.Status.SHIPPED, shipped_at=timezone.now() - timedelta(days=40))
        self.assertNotIn(old.id, self._ids(self.client.get("/api/orders/", {"shipped_within_days": 21})))

    def test_old_shipped_order_included_when_param_absent(self):
        old = self._order(Order.Status.SHIPPED, shipped_at=timezone.now() - timedelta(days=40))
        self.assertIn(old.id, self._ids(self.client.get("/api/orders/")))

    def test_old_shipped_order_included_when_window_wide_enough(self):
        old = self._order(Order.Status.SHIPPED, shipped_at=timezone.now() - timedelta(days=40))
        self.assertIn(old.id, self._ids(self.client.get("/api/orders/", {"shipped_within_days": 90})))

    def test_recent_shipped_order_included_in_windowed_fetch(self):
        recent = self._order(Order.Status.SHIPPED, shipped_at=timezone.now() - timedelta(days=5))
        self.assertIn(recent.id, self._ids(self.client.get("/api/orders/", {"shipped_within_days": 21})))

    def test_shipped_order_with_null_shipped_at_excluded_from_window(self):
        legacy = self._order(Order.Status.SHIPPED, shipped_at=None)
        self.assertNotIn(legacy.id, self._ids(self.client.get("/api/orders/", {"shipped_within_days": 21})))

    def test_window_never_filters_non_shipped_orders_regardless_of_age_or_due_date(self):
        for status in [Order.Status.PENDING, Order.Status.CUTTING, Order.Status.STITCHING, Order.Status.QUALITY_CHECK]:
            order = self._order(status, due_date=timezone.now().date() - timedelta(days=90), age_days=200)
            self.assertIn(
                order.id,
                self._ids(self.client.get("/api/orders/", {"shipped_within_days": 21})),
                f"{status} order should never be touched by the shipped window",
            )

    def test_invalid_window_param_returns_400(self):
        response = self.client.get("/api/orders/", {"shipped_within_days": "banana"})
        self.assertEqual(response.status_code, 400)

    def test_negative_window_param_returns_400(self):
        response = self.client.get("/api/orders/", {"shipped_within_days": -3})
        self.assertEqual(response.status_code, 400)
