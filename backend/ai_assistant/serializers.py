from rest_framework import serializers

from .models import StockAlert


class StockAlertSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    sku = serializers.CharField(source="product.sku", read_only=True)
    order_status = serializers.CharField(source="order.status", read_only=True, default=None)

    class Meta:
        model = StockAlert
        fields = [
            "id", "product", "product_name", "sku", "order", "order_status", "severity",
            "current_stock_at_alert", "reorder_threshold_at_alert", "suggested_quantity",
            "resolved", "created_at",
        ]
        read_only_fields = [
            "id", "product", "order", "severity", "current_stock_at_alert",
            "reorder_threshold_at_alert", "suggested_quantity", "created_at",
        ]
