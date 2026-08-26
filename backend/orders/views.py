import logging

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsOwnerOrInventoryManager

from .models import Order
from .serializers import OrderSerializer, OrderStatusUpdateSerializer

logger = logging.getLogger(__name__)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related("customer").prefetch_related("items__product").all()
    serializer_class = OrderSerializer
    permission_classes = [IsOwnerOrInventoryManager]
    filterset_fields = ["status", "customer"]
    search_fields = ["customer__name"]
    ordering_fields = ["due_date", "created_at"]

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order.status = serializer.validated_data["status"]
        order.save(update_fields=["status", "updated_at"])

        try:
            from ai_assistant.services.agent import evaluate_order_stock

            evaluate_order_stock(order)
        except Exception:
            logger.exception("AI stock evaluation failed for order %s; status change was still saved.", order.id)

        return Response(OrderSerializer(order).data)
