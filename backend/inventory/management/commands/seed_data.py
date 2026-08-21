import datetime
import random

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from ai_assistant.models import StockAlert
from inventory.models import Brand, Category, Product, Warehouse
from orders.models import Order, OrderItem
from partners.models import Customer, Supplier
from transactions.services import create_purchase, create_sale


class Command(BaseCommand):
    help = "Seed the database with realistic FAWNIC leather-goods demo data."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding FAWNIC demo data...")

        users = self._seed_users()
        categories = self._seed_categories()
        brands = self._seed_brands()
        warehouses = self._seed_warehouses()
        products = self._seed_products(categories, brands, warehouses)
        suppliers = self._seed_suppliers()
        customers = self._seed_customers()
        self._seed_purchases(suppliers, products)
        self._seed_sales(customers, products)
        self._seed_orders(customers, products)

        self.stdout.write(self.style.SUCCESS("Seed data created successfully."))

    def _seed_users(self):
        specs = [
            ("owner", "Owner@12345", User.Role.OWNER, True, True),
            ("manager", "Manager@12345", User.Role.INVENTORY_MANAGER, True, False),
            ("support", "Support@12345", User.Role.SUPPORT, False, False),
        ]
        users = {}
        for username, password, role, is_staff, is_superuser in specs:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@fawnic.com",
                    "role": role,
                    "is_staff": is_staff,
                    "is_superuser": is_superuser,
                    "first_name": username.capitalize(),
                },
            )
            if created:
                user.set_password(password)
                user.save()
            users[username] = user
        return users

    def _seed_categories(self):
        names = ["Wallets", "Belts", "Bags", "Leather Materials", "Hardware"]
        return {name: Category.objects.get_or_create(name=name, defaults={"description": f"{name} product line"})[0] for name in names}

    def _seed_brands(self):
        names = ["FAWNIC Classic", "FAWNIC Premium", "FAWNIC Atelier"]
        return {name: Brand.objects.get_or_create(name=name, defaults={"description": f"{name} collection"})[0] for name in names}

    def _seed_warehouses(self):
        specs = [
            ("Main Warehouse — Lagos", "Ikeja Industrial Estate, Lagos", "Primary finished-goods storage"),
            ("Production Store — Aba", "Aba Leather Cluster, Abia State", "Raw materials & work-in-progress"),
        ]
        warehouses = {}
        for name, location, notes in specs:
            warehouses[name] = Warehouse.objects.get_or_create(
                name=name, defaults={"location": location, "capacity_notes": notes}
            )[0]
        return warehouses

    def _seed_products(self, categories, brands, warehouses):
        main_wh = warehouses["Main Warehouse — Lagos"]
        prod_wh = warehouses["Production Store — Aba"]

        specs = [
            # sku, name, category, brand, warehouse, qty, unit_cost, reorder_threshold
            ("FWN-WAL-001", "Classic Bifold Wallet", "Wallets", "FAWNIC Classic", main_wh, 84, 18.50, 20),
            ("FWN-WAL-002", "Slim Card Holder", "Wallets", "FAWNIC Classic", main_wh, 6, 9.75, 15),
            ("FWN-WAL-003", "Premium Trifold Wallet", "Wallets", "FAWNIC Premium", main_wh, 42, 26.00, 15),
            ("FWN-WAL-004", "Atelier Zip-Around Wallet", "Wallets", "FAWNIC Atelier", main_wh, 0, 34.00, 10),
            ("FWN-BLT-001", "Classic Leather Belt", "Belts", "FAWNIC Classic", main_wh, 55, 21.00, 20),
            ("FWN-BLT-002", "Reversible Leather Belt", "Belts", "FAWNIC Premium", main_wh, 12, 28.50, 15),
            ("FWN-BAG-001", "Leather Tote Bag", "Bags", "FAWNIC Premium", main_wh, 23, 78.00, 10),
            ("FWN-BAG-002", "Messenger Bag", "Bags", "FAWNIC Atelier", main_wh, 4, 95.00, 8),
            ("FWN-BAG-003", "Weekender Duffel Bag", "Bags", "FAWNIC Atelier", main_wh, 17, 132.00, 6),
            ("FWN-MAT-001", "Full-Grain Leather Hide", "Leather Materials", "FAWNIC Classic", prod_wh, 30, 145.00, 10),
            ("FWN-MAT-002", "Waxed Cotton Thread (Spool)", "Leather Materials", "FAWNIC Classic", prod_wh, 8, 4.20, 25),
            ("FWN-MAT-003", "Suede Lining Material (m)", "Leather Materials", "FAWNIC Premium", prod_wh, 60, 6.80, 20),
            ("FWN-HW-001", "Brass Belt Buckle", "Hardware", "FAWNIC Classic", prod_wh, 3, 3.10, 30),
            ("FWN-HW-002", "Nickel Zipper Set", "Hardware", "FAWNIC Premium", prod_wh, 90, 2.40, 40),
            ("FWN-HW-003", "Magnetic Snap Closure", "Hardware", "FAWNIC Atelier", prod_wh, 0, 1.85, 25),
        ]

        products = {}
        for sku, name, category_name, brand_name, warehouse, qty, unit_cost, reorder_threshold in specs:
            product, _ = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "category": categories[category_name],
                    "brand": brands[brand_name],
                    "warehouse": warehouse,
                    "quantity": qty,
                    "unit_cost": unit_cost,
                    "reorder_threshold": reorder_threshold,
                },
            )
            products[sku] = product
        return products

    def _seed_suppliers(self):
        specs = [
            ("Lagos Leather Supply Co.", "Adaeze Nwosu", "sales@lagosleather.ng", "+234-801-555-0110"),
            ("Kano Tannery Ltd.", "Ibrahim Musa", "orders@kanotannery.com", "+234-802-555-0142"),
            ("Bronze Hardware Imports", "Chuka Eze", "info@bronzehardware.com", "+234-803-555-0198"),
        ]
        suppliers = {}
        for name, contact, email, phone in specs:
            suppliers[name] = Supplier.objects.get_or_create(
                name=name, defaults={"contact_name": contact, "email": email, "phone": phone}
            )[0]
        return suppliers

    def _seed_customers(self):
        specs = [
            ("Heritage Boutique", "orders@heritageboutique.com", "+234-701-555-0111"),
            ("Adaora Okafor", "adaora.okafor@gmail.com", "+234-802-555-0122"),
            ("Lagos Menswear Collective", "wholesale@lmcollective.com", "+234-803-555-0133"),
            ("Tunde Bakare", "tunde.bakare@yahoo.com", "+234-704-555-0144"),
        ]
        customers = {}
        for name, email, phone in specs:
            customers[name] = Customer.objects.get_or_create(name=name, defaults={"email": email, "phone": phone})[0]
        return customers

    def _seed_purchases(self, suppliers, products):
        today = datetime.date.today()
        create_purchase(
            supplier=suppliers["Lagos Leather Supply Co."],
            date=today - datetime.timedelta(days=12),
            items=[
                {"product": products["FWN-MAT-001"], "quantity": 20, "unit_cost": 145.00},
                {"product": products["FWN-MAT-003"], "quantity": 40, "unit_cost": 6.80},
            ],
        )
        create_purchase(
            supplier=suppliers["Bronze Hardware Imports"],
            date=today - datetime.timedelta(days=6),
            items=[
                {"product": products["FWN-HW-002"], "quantity": 60, "unit_cost": 2.40},
                {"product": products["FWN-HW-001"], "quantity": 10, "unit_cost": 3.10},
            ],
        )
        create_purchase(
            supplier=suppliers["Kano Tannery Ltd."],
            date=today - datetime.timedelta(days=2),
            items=[
                {"product": products["FWN-MAT-002"], "quantity": 15, "unit_cost": 4.20},
            ],
        )

    def _seed_sales(self, customers, products):
        today = datetime.date.today()
        random.seed(42)

        sales_specs = [
            ("Heritage Boutique", 25, [("FWN-WAL-001", 3, 32.00), ("FWN-BLT-001", 2, 38.00)]),
            ("Adaora Okafor", 18, [("FWN-BAG-001", 1, 145.00)]),
            ("Lagos Menswear Collective", 11, [("FWN-WAL-003", 4, 48.00), ("FWN-HW-002", 5, 5.00)]),
            ("Tunde Bakare", 4, [("FWN-BLT-002", 1, 52.00)]),
            ("Heritage Boutique", 1, [("FWN-WAL-001", 2, 32.00)]),
        ]
        for customer_name, days_ago, items in sales_specs:
            create_sale(
                customer=customers[customer_name],
                date=today - datetime.timedelta(days=days_ago),
                items=[{"product": products[sku], "quantity": qty, "unit_price": price} for sku, qty, price in items],
            )

        # A little extra day-by-day sales noise across the last 30 days for the chart.
        chart_products = ["FWN-WAL-001", "FWN-BLT-001", "FWN-BAG-001", "FWN-HW-002"]
        for offset in range(1, 30, 3):
            sku = random.choice(chart_products)
            product = products[sku]
            qty = random.randint(1, 2)
            if product.quantity >= qty:
                create_sale(
                    customer=random.choice(list(customers.values())),
                    date=today - datetime.timedelta(days=offset),
                    items=[{"product": product, "quantity": qty, "unit_price": float(product.unit_cost) * 1.6}],
                )

    def _seed_orders(self, customers, products):
        today = datetime.date.today()
        specs = [
            ("Heritage Boutique", Order.Status.PENDING, 10, [("FWN-WAL-002", 10)]),
            ("Adaora Okafor", Order.Status.CUTTING, 5, [("FWN-MAT-001", 4), ("FWN-HW-001", 6)]),
            ("Lagos Menswear Collective", Order.Status.STITCHING, 7, [("FWN-BAG-002", 8)]),
            ("Tunde Bakare", Order.Status.QUALITY_CHECK, 2, [("FWN-BLT-001", 3)]),
            ("Heritage Boutique", Order.Status.SHIPPED, -3, [("FWN-WAL-001", 5)]),
            ("Lagos Menswear Collective", Order.Status.PENDING, 14, [("FWN-WAL-004", 6), ("FWN-HW-003", 12)]),
        ]
        for customer_name, status, due_offset, items in specs:
            order, created = Order.objects.get_or_create(
                customer=customers[customer_name],
                status=status,
                due_date=today + datetime.timedelta(days=due_offset),
                defaults={},
            )
            if created:
                OrderItem.objects.bulk_create(
                    [OrderItem(order=order, product=products[sku], quantity=qty) for sku, qty in items]
                )
