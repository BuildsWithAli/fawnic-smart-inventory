from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from inventory.models import Brand, Category, Product, Warehouse
from orders.models import Order, OrderItem
from partners.models import Customer

from .models import User


def make_user(role, username):
    return User.objects.create_user(username=username, password="Test@12345", role=role)


def make_product(sku="FWN-TEST-001"):
    category, _ = Category.objects.get_or_create(name="Wallets")
    brand, _ = Brand.objects.get_or_create(name="FAWNIC Classic")
    warehouse, _ = Warehouse.objects.get_or_create(name="Main Warehouse")
    return Product.objects.create(
        sku=sku, name="Test Wallet", category=category, brand=brand,
        warehouse=warehouse, quantity=50, unit_cost=Decimal("10.00"), reorder_threshold=10,
    )


class ProductRolePermissionTests(TestCase):
    """A Support-role user must never be able to write to /api/products/, even
    calling the API directly — the role check happens server-side, in the DRF
    permission class, not merely by hiding buttons in the frontend."""

    def setUp(self):
        self.owner = make_user(User.Role.OWNER, "owner1")
        self.manager = make_user(User.Role.INVENTORY_MANAGER, "manager1")
        self.support = make_user(User.Role.SUPPORT, "support1")
        self.product = make_product()

    def _client_for(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def _payload(self):
        return {
            "sku": "FWN-TEST-002",
            "name": "Another Wallet",
            "category": self.product.category_id,
            "brand": self.product.brand_id,
            "warehouse": self.product.warehouse_id,
            "quantity": 5,
            "unit_cost": "12.00",
            "reorder_threshold": 5,
        }

    def test_support_can_read_but_not_write(self):
        client = self._client_for(self.support)

        self.assertEqual(client.get("/api/products/").status_code, 200)
        self.assertEqual(client.get(f"/api/products/{self.product.id}/").status_code, 200)

        self.assertEqual(client.post("/api/products/", self._payload(), format="json").status_code, 403)
        self.assertEqual(
            client.patch(f"/api/products/{self.product.id}/", {"name": "Hacked"}, format="json").status_code, 403
        )
        self.assertEqual(client.delete(f"/api/products/{self.product.id}/").status_code, 403)

        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Test Wallet")

    def test_support_cannot_adjust_stock(self):
        client = self._client_for(self.support)
        response = client.post(
            f"/api/products/{self.product.id}/adjust-stock/",
            {"new_quantity": 999, "reason": "should be blocked"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 50)

    def test_inventory_manager_has_full_crud(self):
        client = self._client_for(self.manager)

        self.assertEqual(client.get("/api/products/").status_code, 200)
        create = client.post("/api/products/", self._payload(), format="json")
        self.assertEqual(create.status_code, 201)
        new_id = create.data["id"]

        self.assertEqual(client.patch(f"/api/products/{new_id}/", {"name": "Renamed"}, format="json").status_code, 200)
        self.assertEqual(client.delete(f"/api/products/{new_id}/").status_code, 204)

    def test_owner_has_full_crud(self):
        client = self._client_for(self.owner)

        self.assertEqual(client.get("/api/products/").status_code, 200)
        create = client.post("/api/products/", self._payload(), format="json")
        self.assertEqual(create.status_code, 201)


class OrderRolePermissionTests(TestCase):
    """Support may view Orders/Kanban but must not create/edit/delete orders
    or drag a card between columns (PATCH .../status/)."""

    def setUp(self):
        self.owner = make_user(User.Role.OWNER, "owner2")
        self.manager = make_user(User.Role.INVENTORY_MANAGER, "manager2")
        self.support = make_user(User.Role.SUPPORT, "support2")

        self.product = make_product(sku="FWN-TEST-003")
        self.customer = Customer.objects.create(name="Test Customer")
        self.order = Order.objects.create(customer=self.customer, status=Order.Status.PENDING)
        OrderItem.objects.create(order=self.order, product=self.product, quantity=1)

    def _client_for(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def _payload(self):
        return {
            "customer": self.customer.id,
            "items_input": [{"product": self.product.id, "quantity": 1}],
        }

    def test_support_can_view_but_not_mutate_orders(self):
        client = self._client_for(self.support)

        self.assertEqual(client.get("/api/orders/").status_code, 200)
        self.assertEqual(client.get(f"/api/orders/{self.order.id}/").status_code, 200)

        self.assertEqual(client.post("/api/orders/", self._payload(), format="json").status_code, 403)
        self.assertEqual(
            client.patch(f"/api/orders/{self.order.id}/status/", {"status": "cutting"}, format="json").status_code,
            403,
        )
        self.assertEqual(client.delete(f"/api/orders/{self.order.id}/").status_code, 403)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)

    def test_inventory_manager_can_create_and_drag(self):
        client = self._client_for(self.manager)

        create = client.post("/api/orders/", self._payload(), format="json")
        self.assertEqual(create.status_code, 201)

        response = client.patch(f"/api/orders/{self.order.id}/status/", {"status": "cutting"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "cutting")

    def test_owner_can_create_and_drag(self):
        client = self._client_for(self.owner)

        create = client.post("/api/orders/", self._payload(), format="json")
        self.assertEqual(create.status_code, 201)

        response = client.patch(f"/api/orders/{self.order.id}/status/", {"status": "cutting"}, format="json")
        self.assertEqual(response.status_code, 200)
