from django.utils import timezone

from transactions.models import Sale
from transactions.services import create_sale


def create_sale_from_order(order):
    """Creates a Sale from an order's existing customer and line items.

    Reuses transactions.services.create_sale for stock decrement/validation,
    so a shipped order is subject to the same insufficient-stock rules as a
    manually-created Sale.
    """
    items = [
        {"product": item.product, "quantity": item.quantity, "unit_price": item.unit_price}
        for item in order.items.select_related("product").all()
    ]
    sale = create_sale(customer=order.customer, date=timezone.now().date(), items=items, status=Sale.Status.COMPLETED)
    order.generated_sale = sale
    order.save(update_fields=["generated_sale", "updated_at"])
    return sale
