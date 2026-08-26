from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase

from orders.models import Order
from transactions.models import Purchase, Sale

from .models import Brand, Category, Product, Warehouse
from .services import adjust_stock


def make_product(**overrides):
    category, _ = Category.objects.get_or_create(name="Wallets")
    brand, _ = Brand.objects.get_or_create(name="FAWNIC Classic")
    warehouse, _ = Warehouse.objects.get_or_create(name="Main Warehouse")
    defaults = dict(
        sku="FWN-TEST-001",
        name="Test Wallet",
        category=category,
        brand=brand,
        warehouse=warehouse,
        quantity=50,
        unit_cost=Decimal("10.00"),
        reorder_threshold=10,
    )
    defaults.update(overrides)
    return Product.objects.create(**defaults)


class ProductModelTests(TestCase):
    def test_product_creation(self):
        product = make_product()
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(product.sku, "FWN-TEST-001")

    def test_stock_status_thresholds(self):
        in_stock = make_product(sku="A", quantity=50, reorder_threshold=10)
        low_stock = make_product(sku="B", quantity=10, reorder_threshold=10)
        out_of_stock = make_product(sku="C", quantity=0, reorder_threshold=10)

        self.assertEqual(in_stock.stock_status, "in_stock")
        self.assertEqual(low_stock.stock_status, "low_stock")
        self.assertEqual(out_of_stock.stock_status, "out_of_stock")

    def test_inventory_value(self):
        product = make_product(quantity=10, unit_cost=Decimal("5.00"))
        self.assertEqual(product.inventory_value, Decimal("50.00"))


class StockAdjustmentTests(TestCase):
    def test_adjust_stock_creates_audit_trail(self):
        product = make_product(quantity=20)
        adjustment = adjust_stock(product=product, new_quantity=15, reason="Damaged goods", user=None)

        product.refresh_from_db()
        self.assertEqual(product.quantity, 15)
        self.assertEqual(adjustment.previous_quantity, 20)
        self.assertEqual(adjustment.new_quantity, 15)
        self.assertEqual(adjustment.difference, -5)
        self.assertEqual(adjustment.reason, "Damaged goods")


class SeedDataIdempotencyTests(TestCase):
    def test_running_seed_data_twice_does_not_duplicate_purchases_or_sales(self):
        call_command("seed_data")
        purchase_count = Purchase.objects.count()
        sale_count = Sale.objects.count()
        order_count = Order.objects.count()
        product_quantities = {p.sku: p.quantity for p in Product.objects.all()}

        call_command("seed_data")

        self.assertEqual(Purchase.objects.count(), purchase_count)
        self.assertEqual(Sale.objects.count(), sale_count)
        self.assertEqual(Order.objects.count(), order_count)
        self.assertEqual({p.sku: p.quantity for p in Product.objects.all()}, product_quantities)
