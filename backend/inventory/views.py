from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsOwnerOrInventoryManager

from .models import Brand, Category, Product, StockAdjustment, Warehouse
from .serializers import (
    BrandSerializer,
    CategorySerializer,
    ProductSerializer,
    StockAdjustmentCreateSerializer,
    StockAdjustmentSerializer,
    WarehouseSerializer,
)
from .services import adjust_stock


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsOwnerOrInventoryManager]
    search_fields = ["name"]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsOwnerOrInventoryManager]
    search_fields = ["name"]


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsOwnerOrInventoryManager]
    search_fields = ["name", "location"]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category", "brand", "warehouse").all()
    serializer_class = ProductSerializer
    permission_classes = [IsOwnerOrInventoryManager]
    filterset_fields = ["category", "brand", "warehouse"]
    search_fields = ["name", "sku"]
    ordering_fields = ["name", "quantity", "unit_cost", "created_at"]

    @action(detail=True, methods=["post"], url_path="adjust-stock")
    def adjust_stock(self, request, pk=None):
        product = self.get_object()
        serializer = StockAdjustmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        adjustment = adjust_stock(
            product=product,
            new_quantity=serializer.validated_data["new_quantity"],
            reason=serializer.validated_data["reason"],
            user=request.user,
        )
        return Response(StockAdjustmentSerializer(adjustment).data, status=201)

    @action(detail=True, methods=["get"], url_path="stock-history")
    def stock_history(self, request, pk=None):
        product = self.get_object()
        history = product.stock_adjustments.select_related("user").all()
        return Response(StockAdjustmentSerializer(history, many=True).data)


class StockAdjustmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockAdjustment.objects.select_related("product", "user").all()
    serializer_class = StockAdjustmentSerializer
    permission_classes = [IsOwnerOrInventoryManager]
    filterset_fields = ["product"]
    ordering_fields = ["created_at"]
