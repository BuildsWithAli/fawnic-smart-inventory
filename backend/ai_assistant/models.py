from django.db import models

from inventory.models import Product
from orders.models import Order


class StockAlert(models.Model):
    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_alerts")
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, related_name="stock_alerts", null=True, blank=True)
    severity = models.CharField(max_length=16, choices=Severity.choices)
    suggested_quantity = models.PositiveIntegerField(null=True, blank=True)

    # Snapshot of the real, tool-retrieved numbers at the moment the alert was raised —
    # proof the alert was grounded in an actual DB read, not an invented figure.
    current_stock_at_alert = models.PositiveIntegerField()
    reorder_threshold_at_alert = models.PositiveIntegerField()

    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # At most one open (unresolved) alert per product per order. Guards
            # against a timed-out AI provider rung's abandoned worker thread
            # stacking a duplicate alert after a later rung already flagged the
            # same order. Order-less alerts are exempt — they have no such key.
            models.UniqueConstraint(
                fields=["product", "order"],
                condition=models.Q(resolved=False, order__isnull=False),
                name="uniq_open_stockalert_per_product_order",
            ),
        ]

    def __str__(self):
        return f"StockAlert({self.product.sku}, {self.severity})"
