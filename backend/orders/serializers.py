from rest_framework import serializers

from inventory.models import Product

from .models import Order, OrderItem


class OrderItemReadSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    sku = serializers.CharField(source="product.sku", read_only=True)
    stock_status = serializers.CharField(source="product.stock_status", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "sku", "quantity", "unit_price", "stock_status"]


class OrderItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)
    items_input = OrderItemWriteSerializer(many=True, write_only=True, required=False)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    active_alerts_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "customer", "customer_name", "items", "items_input", "status",
            "due_date", "shipped_at", "active_alerts_count", "generated_sale",
            "created_at", "updated_at",
        ]
        read_only_fields = ["generated_sale", "shipped_at"]

    def get_active_alerts_count(self, obj):
        return obj.stock_alerts.filter(resolved=False).count()

    def create(self, validated_data):
        items = validated_data.pop("items_input", [])
        order = Order.objects.create(**validated_data)
        OrderItem.objects.bulk_create(
            [
                OrderItem(order=order, product=item["product"], quantity=item["quantity"], unit_price=item["unit_price"])
                for item in items
            ]
        )
        return order

    def update(self, instance, validated_data):
        items = validated_data.pop("items_input", None)
        instance = super().update(instance, validated_data)
        if items is not None:
            instance.items.all().delete()
            OrderItem.objects.bulk_create(
                [
                    OrderItem(
                        order=instance, product=item["product"], quantity=item["quantity"], unit_price=item["unit_price"]
                    )
                    for item in items
                ]
            )
        return instance


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
