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


@transaction.atomic
def delete_purchase(purchase):
    """Deletes a Purchase and reverses the stock increase it applied, atomically.

    Raises ValidationError if reversing any line item would drive a product's
    quantity below zero (its purchased stock has since been sold or adjusted away).
    """
    items = list(purchase.items.select_related("product").all())

    locked = {}
    for item in items:
        product = locked.get(item.product_id)
        if product is None:
            product = Product.objects.select_for_update().get(pk=item.product_id)
            locked[item.product_id] = product
        product.quantity -= item.quantity

    for product in locked.values():
        if product.quantity < 0:
            raise ValidationError(
                f"Can't delete this purchase: stock for {product.name} ({product.sku}) "
                "has since been sold or adjusted, so reversing it would make the quantity negative."
            )

    for product in locked.values():
        product.save(update_fields=["quantity", "updated_at"])

    purchase.delete()


@transaction.atomic
def delete_sale(sale):
    """Deletes a Sale and restores the stock it deducted, atomically.

    If the Sale was auto-generated from a shipped Order, that Order's
    ``generated_sale`` link is cleared by the FK's on_delete=SET_NULL.
    """
    items = list(sale.items.select_related("product").all())

    locked = {}
    for item in items:
        product = locked.get(item.product_id)
        if product is None:
            product = Product.objects.select_for_update().get(pk=item.product_id)
            locked[item.product_id] = product
        product.quantity += item.quantity

    for product in locked.values():
        product.save(update_fields=["quantity", "updated_at"])

    sale.delete()
