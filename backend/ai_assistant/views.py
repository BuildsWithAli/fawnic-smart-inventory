from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsOwnerOrInventoryManager

from .models import StockAlert
from .serializers import StockAlertSerializer


class StockAlertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockAlert.objects.select_related("product", "order").all()
    serializer_class = StockAlertSerializer
    permission_classes = [IsOwnerOrInventoryManager]
    filterset_fields = ["resolved", "severity", "product", "order"]
    ordering_fields = ["created_at"]

    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        alert = self.get_object()
        alert.resolved = True
        alert.save(update_fields=["resolved"])
        return Response(StockAlertSerializer(alert).data)
