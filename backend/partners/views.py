from django.db.models import ProtectedError
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from accounts.permissions import IsOwnerOrInventoryManager

from .models import Customer, Supplier
from .serializers import CustomerSerializer, SupplierSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsOwnerOrInventoryManager]
    search_fields = ["name", "contact_name", "email"]

    def perform_destroy(self, instance):
        """Supplier is on_delete=PROTECT on Purchase — turn the raw ProtectedError
        into a clear, specific message instead of a generic 500."""
        try:
            instance.delete()
        except ProtectedError:
            count = instance.purchases.count()
            raise ValidationError(
                f"Can't delete {instance.name} — they have {count} purchase"
                f"{'s' if count != 1 else ''} on record. Remove or reassign "
                "those purchases first."
            )


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsOwnerOrInventoryManager]
    search_fields = ["name", "email"]

    def perform_destroy(self, instance):
        """Customer is on_delete=PROTECT on Sale — turn the raw ProtectedError
        into a clear, specific message instead of a generic 500."""
        try:
            instance.delete()
        except ProtectedError:
            count = instance.sales.count()
            raise ValidationError(
                f"Can't delete {instance.name} — they have {count} sale"
                f"{'s' if count != 1 else ''} on record. Remove or reassign "
                "those sales first."
            )
