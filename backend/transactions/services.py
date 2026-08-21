from django.db import transaction
from rest_framework.exceptions import ValidationError

from inventory.models import Product

from .models import Purchase, PurchaseItem, Sale, SaleItem


@transaction.atomic
def create_purchase(*, supplier, date, items):
    """items: list of {product, quantity, unit_cost}. Increases stock atomically."""
    purchase = Purchase.objects.create(supplier=supplier, date=date)

    purchase_items = []
    for item in items:
        product = Product.objects.select_for_update().get(pk=item["product"].pk)
        product.quantity += item["quantity"]
        product.save(update_fields=["quantity", "updated_at"])
        purchase_items.append(
            PurchaseItem(
                purchase=purchase,
                product=product,
                quantity=item["quantity"],
                unit_cost=item["unit_cost"],
            )
        )
    PurchaseItem.objects.bulk_create(purchase_items)
    return purchase


@transaction.atomic
def create_sale(*, customer, date, items, status=Sale.Status.COMPLETED):
    """items: list of {product, quantity, unit_price}. Decreases stock atomically.

    Raises ValidationError if any line item would take a product's quantity below zero.
    """
    sale = Sale.objects.create(customer=customer, date=date, status=status)

    sale_items = []
    for item in items:
        product = Product.objects.select_for_update().get(pk=item["product"].pk)
        if item["quantity"] > product.quantity:
            raise ValidationError(
                f"Insufficient stock for {product.name} ({product.sku}): "
                f"requested {item['quantity']}, available {product.quantity}."
            )
        product.quantity -= item["quantity"]
        product.save(update_fields=["quantity", "updated_at"])
        sale_items.append(
            SaleItem(
                sale=sale,
                product=product,
                quantity=item["quantity"],
                unit_price=item["unit_price"],
            )
        )
    SaleItem.objects.bulk_create(sale_items)
    return sale
