from django.db import transaction

from .models import Product, StockAdjustment


@transaction.atomic
def adjust_stock(*, product: Product, new_quantity: int, reason: str, user):
    product = Product.objects.select_for_update().get(pk=product.pk)
    previous_quantity = product.quantity
    difference = new_quantity - previous_quantity

    product.quantity = new_quantity
    product.save(update_fields=["quantity", "updated_at"])

    return StockAdjustment.objects.create(
        product=product,
        previous_quantity=previous_quantity,
        new_quantity=new_quantity,
        difference=difference,
        reason=reason,
        user=user,
    )
