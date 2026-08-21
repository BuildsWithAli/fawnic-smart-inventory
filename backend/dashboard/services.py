from datetime import timedelta
from decimal import Decimal

from django.db.models import Case, DecimalField, F, IntegerField, Sum, When
from django.utils import timezone

from inventory.models import Brand, Category, Product, Warehouse
from orders.models import Order
from partners.models import Supplier
from transactions.models import Purchase, PurchaseItem, Sale, SaleItem


def get_kpis():
    stock_counts = Product.objects.aggregate(
        total=Sum(Case(When(pk__isnull=False, then=1), default=0, output_field=IntegerField())),
        low_stock=Sum(
            Case(
                When(quantity__gt=0, quantity__lte=F("reorder_threshold"), then=1),
                default=0,
                output_field=IntegerField(),
            )
        ),
        out_of_stock=Sum(Case(When(quantity__lte=0, then=1), default=0, output_field=IntegerField())),
        inventory_value=Sum(
            F("quantity") * F("unit_cost"), output_field=DecimalField(max_digits=14, decimal_places=2)
        ),
    )

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_revenue = (
        SaleItem.objects.filter(sale__date__gte=month_start.date(), sale__status=Sale.Status.COMPLETED)
        .aggregate(
            total=Sum(F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=14, decimal_places=2))
        )
        .get("total")
        or Decimal("0.00")
    )

    return {
        "total_products": stock_counts["total"] or 0,
        "low_stock": stock_counts["low_stock"] or 0,
        "out_of_stock": stock_counts["out_of_stock"] or 0,
        "warehouses": Warehouse.objects.count(),
        "categories": Category.objects.count(),
        "brands": Brand.objects.count(),
        "suppliers": Supplier.objects.count(),
        "purchase_orders": Purchase.objects.count(),
        "sales_orders": Sale.objects.count(),
        "monthly_revenue": monthly_revenue,
        "inventory_value": stock_counts["inventory_value"] or Decimal("0.00"),
    }


def get_sales_vs_purchases(days=30):
    today = timezone.localdate()
    start_date = today - timedelta(days=days - 1)

    sales_by_day = dict(
        SaleItem.objects.filter(sale__date__gte=start_date, sale__status=Sale.Status.COMPLETED)
        .values("sale__date")
        .annotate(total=Sum(F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=14, decimal_places=2)))
        .values_list("sale__date", "total")
    )
    purchases_by_day = dict(
        PurchaseItem.objects.filter(purchase__date__gte=start_date)
        .values("purchase__date")
        .annotate(total=Sum(F("quantity") * F("unit_cost"), output_field=DecimalField(max_digits=14, decimal_places=2)))
        .values_list("purchase__date", "total")
    )

    series = []
    for offset in range(days):
        day = start_date + timedelta(days=offset)
        series.append(
            {
                "date": day.isoformat(),
                "sales": sales_by_day.get(day, Decimal("0.00")),
                "purchases": purchases_by_day.get(day, Decimal("0.00")),
            }
        )
    return series


def get_stock_health():
    counts = Product.objects.aggregate(
        in_stock=Sum(Case(When(quantity__gt=F("reorder_threshold"), then=1), default=0, output_field=IntegerField())),
        low_stock=Sum(
            Case(
                When(quantity__gt=0, quantity__lte=F("reorder_threshold"), then=1),
                default=0,
                output_field=IntegerField(),
            )
        ),
        out_of_stock=Sum(Case(When(quantity__lte=0, then=1), default=0, output_field=IntegerField())),
    )
    return {
        "in_stock": counts["in_stock"] or 0,
        "low_stock": counts["low_stock"] or 0,
        "out_of_stock": counts["out_of_stock"] or 0,
    }


def get_recent_sales(limit=5):
    sales = Sale.objects.select_related("customer").prefetch_related("items")[:limit]
    return [
        {
            "id": sale.id,
            "customer": sale.customer.name,
            "amount": sale.total,
            "date": sale.date.isoformat(),
            "status": sale.status,
        }
        for sale in sales
    ]


def get_recent_purchases(limit=5):
    purchases = Purchase.objects.select_related("supplier").prefetch_related("items")[:limit]
    return [
        {
            "id": purchase.id,
            "supplier": purchase.supplier.name,
            "amount": purchase.total,
            "date": purchase.date.isoformat(),
        }
        for purchase in purchases
    ]


def get_low_stock_products(limit=8):
    products = (
        Product.objects.filter(quantity__lte=F("reorder_threshold"))
        .select_related("category")
        .order_by("quantity")[:limit]
    )
    return [
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "quantity": p.quantity,
            "reorder_threshold": p.reorder_threshold,
            "stock_status": p.stock_status,
        }
        for p in products
    ]


def get_recent_orders(limit=5):
    orders = Order.objects.select_related("customer")[:limit]
    return [
        {
            "id": order.id,
            "customer": order.customer.name,
            "status": order.status,
            "due_date": order.due_date.isoformat() if order.due_date else None,
        }
        for order in orders
    ]


def get_dashboard_data():
    return {
        "kpis": get_kpis(),
        "sales_vs_purchases": get_sales_vs_purchases(),
        "stock_health": get_stock_health(),
        "recent_sales": get_recent_sales(),
        "recent_purchases": get_recent_purchases(),
        "low_stock_products": get_low_stock_products(),
        "recent_orders": get_recent_orders(),
    }
