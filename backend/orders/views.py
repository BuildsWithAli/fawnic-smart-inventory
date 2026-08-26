import logging

from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsOwnerOrInventoryManager

from .models import Order
from .serializers import OrderSerializer, OrderStatusUpdateSerializer
from .services import create_sale_from_order

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
        new_status = serializer.validated_data["status"]

        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=order.pk)
            previous_status = order.status
            order.status = new_status
            order.save(update_fields=["status", "updated_at"])

            if (
                new_status == Order.Status.SHIPPED
                and previous_status != Order.Status.SHIPPED
                and order.generated_sale_id is None
            ):
                create_sale_from_order(order)

        try:
            from ai_assistant.services.agent import evaluate_order_stock

            evaluate_order_stock(order)
        except Exception:
            logger.exception("AI stock evaluation failed for order %s; status change was still saved.", order.id)

        return Response(OrderSerializer(order).data)
