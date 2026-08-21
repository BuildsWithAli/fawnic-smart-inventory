from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from inventory.models import Brand, Category, Product, Warehouse
from partners.models import Customer

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
        response = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "cutting"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "cutting")
        mock_evaluate.assert_called_once_with(self.order)

    @patch("ai_assistant.services.agent.evaluate_order_stock", side_effect=RuntimeError("provider down"))
    def test_status_update_succeeds_even_if_ai_check_fails(self, mock_evaluate):
        response = self.client.patch(f"/api/orders/{self.order.id}/status/", {"status": "cutting"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "cutting")
