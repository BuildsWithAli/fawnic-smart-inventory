import datetime
from decimal import Decimal

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from inventory.models import Brand, Category, Product, Warehouse
from partners.models import Customer, Supplier

from .models import Sale
from .services import create_purchase, create_sale


class TransactionServiceTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Wallets")
        brand = Brand.objects.create(name="FAWNIC Classic")
        warehouse = Warehouse.objects.create(name="Main Warehouse")
        self.product = Product.objects.create(
            sku="FWN-TEST-001",
            name="Test Wallet",
            category=category,
            brand=brand,
            warehouse=warehouse,
            quantity=10,
            unit_cost=Decimal("10.00"),
            reorder_threshold=5,
        )
        self.supplier = Supplier.objects.create(name="Test Supplier")
        self.customer = Customer.objects.create(name="Test Customer")

    def test_purchase_increases_stock(self):
        create_purchase(
            supplier=self.supplier,
            date=datetime.date.today(),
            items=[{"product": self.product, "quantity": 15, "unit_cost": Decimal("9.50")}],
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 25)

    def test_sale_decreases_stock(self):
        create_sale(
            customer=self.customer,
            date=datetime.date.today(),
            items=[{"product": self.product, "quantity": 4, "unit_price": Decimal("20.00")}],
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 6)

    def test_insufficient_stock_raises_and_does_not_partially_commit(self):
        with self.assertRaises(ValidationError):
            create_sale(
                customer=self.customer,
                date=datetime.date.today(),
                items=[{"product": self.product, "quantity": 999, "unit_price": Decimal("20.00")}],
            )
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 10)
        self.assertEqual(Sale.objects.count(), 0)

    def test_sale_total_is_sum_of_line_items(self):
        sale = create_sale(
            customer=self.customer,
            date=datetime.date.today(),
            items=[{"product": self.product, "quantity": 3, "unit_price": Decimal("20.00")}],
        )
        self.assertEqual(sale.total, Decimal("60.00"))
