from rest_framework import viewsets

from accounts.permissions import IsOwnerOrInventoryManager

from .models import Purchase, Sale
from .serializers import PurchaseSerializer, SaleSerializer


class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.select_related("supplier").prefetch_related("items__product").all()
    serializer_class = PurchaseSerializer
    permission_classes = [IsOwnerOrInventoryManager]
    filterset_fields = ["supplier"]
    search_fields = ["supplier__name"]
    ordering_fields = ["date", "created_at"]


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.select_related("customer").prefetch_related("items__product").all()
    serializer_class = SaleSerializer
    permission_classes = [IsOwnerOrInventoryManager]
    filterset_fields = ["customer", "status"]
    search_fields = ["customer__name"]
    ordering_fields = ["date", "created_at"]
