from decimal import Decimal

from django.db import models

from inventory.models import Product
from partners.models import Customer


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CUTTING = "cutting", "Cutting"
        STITCHING = "stitching", "Stitching"
        QUALITY_CHECK = "quality_check", "Quality Check"
        SHIPPED = "shipped", "Shipped"

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    products = models.ManyToManyField(Product, through="OrderItem", related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    due_date = models.DateField(null=True, blank=True)
    generated_sale = models.OneToOneField(
        "transactions.Sale", on_delete=models.SET_NULL, null=True, blank=True, related_name="source_order"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} — {self.customer.name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    def __str__(self):
        return f"{self.product.sku} x{self.quantity}"
