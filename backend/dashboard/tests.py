from decimal import Decimal

from django.test import TestCase

from inventory.models import Brand, Category, Product, Warehouse

from .services import get_kpis, get_stock_health


class DashboardCalculationTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Wallets")
        brand = Brand.objects.create(name="FAWNIC Classic")
        warehouse = Warehouse.objects.create(name="Main Warehouse")

        # in stock
        Product.objects.create(
            sku="A", name="A", category=category, brand=brand, warehouse=warehouse,
            quantity=50, unit_cost=Decimal("10.00"), reorder_threshold=10,
        )
        # low stock
        Product.objects.create(
            sku="B", name="B", category=category, brand=brand, warehouse=warehouse,
            quantity=5, unit_cost=Decimal("4.00"), reorder_threshold=10,
        )
        # out of stock
        Product.objects.create(
            sku="C", name="C", category=category, brand=brand, warehouse=warehouse,
            quantity=0, unit_cost=Decimal("2.00"), reorder_threshold=10,
        )

    def test_stock_health_counts(self):
        health = get_stock_health()
        self.assertEqual(health["in_stock"], 1)
        self.assertEqual(health["low_stock"], 1)
        self.assertEqual(health["out_of_stock"], 1)

    def test_kpi_inventory_value_is_derived_from_real_product_data(self):
        kpis = get_kpis()
        # 50*10.00 + 5*4.00 + 0*2.00 = 500 + 20 + 0 = 520.00
        self.assertEqual(kpis["inventory_value"], Decimal("520.00"))
        self.assertEqual(kpis["total_products"], 3)
        self.assertEqual(kpis["low_stock"], 1)
        self.assertEqual(kpis["out_of_stock"], 1)
