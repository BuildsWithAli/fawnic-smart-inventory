from rest_framework import serializers

from .models import Brand, Category, Product, StockAdjustment, Warehouse


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "description", "created_at", "updated_at"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "created_at", "updated_at"]


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "name", "location", "capacity_notes", "created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    brand_name = serializers.CharField(source="brand.name", read_only=True)
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    stock_status = serializers.CharField(read_only=True)
    inventory_value = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "sku", "name", "category", "category_name", "brand", "brand_name",
            "warehouse", "warehouse_name", "quantity", "unit_cost", "reorder_threshold",
            "stock_status", "inventory_value", "created_at", "updated_at",
        ]


class StockAdjustmentSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    sku = serializers.CharField(source="product.sku", read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True, default=None)

    class Meta:
        model = StockAdjustment
        fields = [
            "id", "product", "product_name", "sku", "previous_quantity", "new_quantity",
            "difference", "reason", "user", "user_name", "created_at",
        ]
        read_only_fields = ["id", "previous_quantity", "difference", "user", "created_at"]


class StockAdjustmentCreateSerializer(serializers.Serializer):
    new_quantity = serializers.IntegerField(min_value=0)
    reason = serializers.CharField(max_length=255)
