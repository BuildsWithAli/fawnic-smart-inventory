from rest_framework import viewsets

from accounts.permissions import IsOwnerOrInventoryManager

from .models import Customer, Supplier
from .serializers import CustomerSerializer, SupplierSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsOwnerOrInventoryManager]
    search_fields = ["name", "contact_name", "email"]


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsOwnerOrInventoryManager]
    search_fields = ["name", "email"]
