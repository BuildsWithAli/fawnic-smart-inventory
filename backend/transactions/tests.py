import datetime
from decimal import Decimal

from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from accounts.models import User
from inventory.models import Brand, Category, Product, Warehouse
from orders.models import Order, OrderItem
from partners.models import Customer, Supplier

from .models import Purchase, Sale
from .services import create_purchase, create_sale, delete_purchase, delete_sale


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


class TransactionReversalOnDeleteTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Wallets")
        brand = Brand.objects.create(name="FAWNIC Classic")
        warehouse = Warehouse.objects.create(name="Main Warehouse")
        self.wallet = Product.objects.create(
            sku="FWN-REV-001", name="Bifold Wallet", category=category, brand=brand,
            warehouse=warehouse, quantity=20, unit_cost=Decimal("10.00"), reorder_threshold=5,
        )
        self.belt = Product.objects.create(
            sku="FWN-REV-002", name="Leather Belt", category=category, brand=brand,
            warehouse=warehouse, quantity=8, unit_cost=Decimal("12.00"), reorder_threshold=3,
        )
        self.supplier = Supplier.objects.create(name="Tannery Co")
        self.customer = Customer.objects.create(name="Boutique Buyer")

    def test_deleting_sale_restores_exact_quantities_it_deducted(self):
        sale = create_sale(
            customer=self.customer,
            date=datetime.date.today(),
            items=[
                {"product": self.wallet, "quantity": 6, "unit_price": Decimal("30.00")},
                {"product": self.belt, "quantity": 3, "unit_price": Decimal("25.00")},
            ],
        )
        self.wallet.refresh_from_db()
        self.belt.refresh_from_db()
        self.assertEqual(self.wallet.quantity, 14)
        self.assertEqual(self.belt.quantity, 5)

        delete_sale(sale)

        self.wallet.refresh_from_db()
        self.belt.refresh_from_db()
        self.assertEqual(self.wallet.quantity, 20)
        self.assertEqual(self.belt.quantity, 8)
        self.assertFalse(Sale.objects.filter(pk=sale.pk).exists())

    def test_deleting_purchase_reverses_exact_quantities_it_added(self):
        purchase = create_purchase(
            supplier=self.supplier,
            date=datetime.date.today(),
            items=[
                {"product": self.wallet, "quantity": 15, "unit_cost": Decimal("9.00")},
                {"product": self.belt, "quantity": 10, "unit_cost": Decimal("11.00")},
            ],
        )
        self.wallet.refresh_from_db()
        self.belt.refresh_from_db()
        self.assertEqual(self.wallet.quantity, 35)
        self.assertEqual(self.belt.quantity, 18)

        delete_purchase(purchase)

        self.wallet.refresh_from_db()
        self.belt.refresh_from_db()
        self.assertEqual(self.wallet.quantity, 20)
        self.assertEqual(self.belt.quantity, 8)
        self.assertFalse(Purchase.objects.filter(pk=purchase.pk).exists())

    def test_deleting_purchase_is_blocked_when_its_stock_was_already_consumed(self):
        purchase = create_purchase(
            supplier=self.supplier,
            date=datetime.date.today(),
            items=[{"product": self.wallet, "quantity": 15, "unit_cost": Decimal("9.00")}],
        )
        create_sale(
            customer=self.customer,
            date=datetime.date.today(),
            items=[{"product": self.wallet, "quantity": 30, "unit_price": Decimal("30.00")}],
        )
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.quantity, 5)

        with self.assertRaises(ValidationError):
            delete_purchase(purchase)

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.quantity, 5)
        self.assertTrue(Purchase.objects.filter(pk=purchase.pk).exists())

    def test_deleting_auto_generated_sale_restores_stock_and_nulls_source_order(self):
        order = Order.objects.create(customer=self.customer, status=Order.Status.SHIPPED)
        OrderItem.objects.create(order=order, product=self.wallet, quantity=4, unit_price=Decimal("30.00"))
        sale = create_sale(
            customer=self.customer,
            date=datetime.date.today(),
            items=[{"product": self.wallet, "quantity": 4, "unit_price": Decimal("30.00")}],
        )
        order.generated_sale = sale
        order.save(update_fields=["generated_sale"])
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.quantity, 16)

        delete_sale(sale)

        self.wallet.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(self.wallet.quantity, 20)
        self.assertIsNone(order.generated_sale_id)
        self.assertEqual(order.status, Order.Status.SHIPPED)


class TransactionDeleteApiPermissionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="rev-owner", password="Test@12345", role=User.Role.OWNER)
        self.support = User.objects.create_user(username="rev-support", password="Test@12345", role=User.Role.SUPPORT)
        self.client = APIClient()

        category = Category.objects.create(name="Wallets")
        brand = Brand.objects.create(name="FAWNIC Classic")
        warehouse = Warehouse.objects.create(name="Main Warehouse")
        self.product = Product.objects.create(
            sku="FWN-REV-API", name="Card Holder", category=category, brand=brand,
            warehouse=warehouse, quantity=50, unit_cost=Decimal("6.00"), reorder_threshold=5,
        )
        self.supplier = Supplier.objects.create(name="Tannery Co")
        self.customer = Customer.objects.create(name="Boutique Buyer")

    def _sale(self):
        return create_sale(
            customer=self.customer, date=datetime.date.today(),
            items=[{"product": self.product, "quantity": 10, "unit_price": Decimal("20.00")}],
        )

    def _purchase(self):
        return create_purchase(
            supplier=self.supplier, date=datetime.date.today(),
            items=[{"product": self.product, "quantity": 10, "unit_cost": Decimal("5.00")}],
        )

    def test_owner_deletes_sale_and_stock_is_restored(self):
        sale = self._sale()
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(f"/api/sales/{sale.id}/")

        self.assertEqual(response.status_code, 204)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 50)
        self.assertFalse(Sale.objects.filter(pk=sale.id).exists())

    def test_support_cannot_delete_sale_and_stock_is_untouched(self):
        sale = self._sale()
        self.client.force_authenticate(user=self.support)

        response = self.client.delete(f"/api/sales/{sale.id}/")

        self.assertEqual(response.status_code, 403)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 40)
        self.assertTrue(Sale.objects.filter(pk=sale.id).exists())

    def test_owner_deletes_purchase_and_stock_is_reversed(self):
        purchase = self._purchase()
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(f"/api/purchases/{purchase.id}/")

        self.assertEqual(response.status_code, 204)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 50)
        self.assertFalse(Purchase.objects.filter(pk=purchase.id).exists())

    def test_support_cannot_delete_purchase_and_stock_is_untouched(self):
        purchase = self._purchase()
        self.client.force_authenticate(user=self.support)

        response = self.client.delete(f"/api/purchases/{purchase.id}/")

        self.assertEqual(response.status_code, 403)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 60)
        self.assertTrue(Purchase.objects.filter(pk=purchase.id).exists())
