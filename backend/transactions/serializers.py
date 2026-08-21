from rest_framework import serializers

from inventory.models import Product
from partners.models import Customer, Supplier

from .models import Purchase, PurchaseItem, Sale, SaleItem
from .services import create_purchase, create_sale


class PurchaseItemReadSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    sku = serializers.CharField(source="product.sku", read_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = PurchaseItem
        fields = ["id", "product", "product_name", "sku", "quantity", "unit_cost", "line_total"]


class PurchaseItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)
    unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)


class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemReadSerializer(many=True, read_only=True)
    items_input = PurchaseItemWriteSerializer(many=True, write_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Purchase
        fields = ["id", "supplier", "supplier_name", "date", "items", "items_input", "total", "created_at"]

    def validate_items_input(self, value):
        if not value:
            raise serializers.ValidationError("At least one line item is required.")
        return value

    def create(self, validated_data):
        items = validated_data.pop("items_input")
        return create_purchase(
            supplier=validated_data["supplier"],
            date=validated_data["date"],
            items=items,
        )


class SaleItemReadSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    sku = serializers.CharField(source="product.sku", read_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = SaleItem
        fields = ["id", "product", "product_name", "sku", "quantity", "unit_price", "line_total"]


class SaleItemWriteSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemReadSerializer(many=True, read_only=True)
    items_input = SaleItemWriteSerializer(many=True, write_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Sale
        fields = ["id", "customer", "customer_name", "date", "status", "items", "items_input", "total", "created_at"]

    def validate_items_input(self, value):
        if not value:
            raise serializers.ValidationError("At least one line item is required.")
        return value

    def create(self, validated_data):
        items = validated_data.pop("items_input")
        return create_sale(
            customer=validated_data["customer"],
            date=validated_data["date"],
            items=items,
            status=validated_data.get("status", Sale.Status.COMPLETED),
        )
