import datetime
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from inventory.models import Brand, Category, Product, Warehouse
from transactions.services import create_purchase, create_sale

from .models import Customer, Supplier


class ProtectedDeleteApiTests(TestCase):
    """Deleting a Customer/Supplier that still has Sales/Purchases must return a
    clean 400 with a specific reason, not an unhandled 500 from ProtectedError."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username="partners-owner", password="Test@12345", role=User.Role.OWNER
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

        category = Category.objects.create(name="Wallets")
        brand = Brand.objects.create(name="FAWNIC Classic")
        warehouse = Warehouse.objects.create(name="Main Warehouse")
        self.product = Product.objects.create(
            sku="FWN-PRT-001", name="Bifold Wallet", category=category, brand=brand,
            warehouse=warehouse, quantity=100, unit_cost=Decimal("10.00"), reorder_threshold=5,
        )

    def test_deleting_customer_with_sales_is_blocked_with_specific_message(self):
        customer = Customer.objects.create(name="Boutique Buyer")
        create_sale(
            customer=customer, date=datetime.date.today(),
            items=[{"product": self.product, "quantity": 2, "unit_price": Decimal("30.00")}],
        )

        response = self.client.delete(f"/api/customers/{customer.id}/")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"],
            "Can't delete Boutique Buyer — they have 1 sale on record. "
            "Remove or reassign those sales first.",
        )
        self.assertTrue(Customer.objects.filter(pk=customer.id).exists())

    def test_deleting_supplier_with_purchases_is_blocked_with_specific_message(self):
        supplier = Supplier.objects.create(name="Tannery Co")
        create_purchase(
            supplier=supplier, date=datetime.date.today(),
            items=[{"product": self.product, "quantity": 5, "unit_cost": Decimal("9.00")}],
        )
        create_purchase(
            supplier=supplier, date=datetime.date.today(),
            items=[{"product": self.product, "quantity": 3, "unit_cost": Decimal("9.50")}],
        )

        response = self.client.delete(f"/api/suppliers/{supplier.id}/")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"],
            "Can't delete Tannery Co — they have 2 purchases on record. "
            "Remove or reassign those purchases first.",
        )
        self.assertTrue(Supplier.objects.filter(pk=supplier.id).exists())

    def test_deleting_customer_without_history_still_works(self):
        customer = Customer.objects.create(name="Walk-in Customer")

        response = self.client.delete(f"/api/customers/{customer.id}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Customer.objects.filter(pk=customer.id).exists())

    def test_deleting_supplier_without_history_still_works(self):
        supplier = Supplier.objects.create(name="Unused Supplier")

        response = self.client.delete(f"/api/suppliers/{supplier.id}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Supplier.objects.filter(pk=supplier.id).exists())
