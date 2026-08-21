"""
The four real, Django-backed functions the AI stock agent is allowed to call.

These are the ONLY way the agent can touch the database. The agent never gets a
database connection, an ORM handle, or raw SQL access — it can only request that
one of these four named functions run, with arguments it supplies. Every argument
is validated here before anything is read or written, and every write is scoped to
exactly what the function name promises (flag_low_stock creates/updates a
StockAlert; suggest_reorder attaches a quantity to one; neither ever touches
Product.quantity).
"""

from inventory.models import Product
from orders.models import Order

from ..models import StockAlert

ALLOWED_SEVERITIES = {choice for choice, _ in StockAlert.Severity.choices}


def get_stock_level(product_id: int) -> dict:
    """Return the real, current on-hand quantity for a product."""
    product = Product.objects.get(pk=product_id)
    return {
        "product_id": product.id,
        "sku": product.sku,
        "name": product.name,
        "quantity": product.quantity,
    }


def get_reorder_threshold(product_id: int) -> dict:
    """Return the real reorder threshold configured for a product."""
    product = Product.objects.get(pk=product_id)
    return {
        "product_id": product.id,
        "reorder_threshold": product.reorder_threshold,
    }


def flag_low_stock(product_id: int, order_id: int, severity: str) -> dict:
    """Create a StockAlert. Snapshots the product's real current stock/threshold
    at creation time so the alert can never be accused of showing invented numbers."""
    if severity not in ALLOWED_SEVERITIES:
        raise ValueError(f"Invalid severity '{severity}'. Must be one of {sorted(ALLOWED_SEVERITIES)}.")

    product = Product.objects.get(pk=product_id)
    order = Order.objects.get(pk=order_id) if order_id is not None else None

    alert = StockAlert.objects.create(
        product=product,
        order=order,
        severity=severity,
        current_stock_at_alert=product.quantity,
        reorder_threshold_at_alert=product.reorder_threshold,
    )
    return {
        "alert_id": alert.id,
        "product_id": product.id,
        "severity": severity,
        "current_stock": product.quantity,
        "reorder_threshold": product.reorder_threshold,
    }


def suggest_reorder(product_id: int, suggested_qty: int) -> dict:
    """Attach a suggested reorder quantity to the most recent unresolved alert for
    this product, creating one first if flag_low_stock hasn't been called yet."""
    if not isinstance(suggested_qty, int) or isinstance(suggested_qty, bool) or suggested_qty <= 0:
        raise ValueError("suggested_qty must be a positive integer.")

    product = Product.objects.get(pk=product_id)
    alert = (
        StockAlert.objects.filter(product=product, resolved=False)
        .order_by("-created_at")
        .first()
    )
    if alert is None:
        alert = StockAlert.objects.create(
            product=product,
            severity=StockAlert.Severity.MEDIUM,
            current_stock_at_alert=product.quantity,
            reorder_threshold_at_alert=product.reorder_threshold,
        )

    alert.suggested_quantity = suggested_qty
    alert.save(update_fields=["suggested_quantity"])
    return {
        "alert_id": alert.id,
        "product_id": product.id,
        "suggested_quantity": suggested_qty,
    }
