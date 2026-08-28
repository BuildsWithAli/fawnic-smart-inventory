import logging

from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
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

    def perform_destroy(self, instance):
        if instance.generated_sale_id is not None:
            raise ValidationError(
                f"Order #{instance.id} has already been converted to Sale #{instance.generated_sale_id} "
                "and can't be deleted."
            )
        instance.delete()

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

        ai_stock_check = "unavailable"
        try:
            from ai_assistant.services.agent import VALID_STOCK_CHECK_STATUSES, evaluate_order_stock

            result = evaluate_order_stock(order)
            status_value = getattr(result, "status", None)
            if status_value in VALID_STOCK_CHECK_STATUSES:
                ai_stock_check = status_value
        except Exception:
            logger.exception("AI stock evaluation failed for order %s; status change was still saved.", order.id)

        # `ai_stock_check` lets the client tell "checked, all fine" (ok) apart from
        # "no check ran" (unavailable) — the latter drove a silent regression where
        # a rate-limited provider produced no alert and nothing surfaced it.
        return Response({**OrderSerializer(order).data, "ai_stock_check": ai_stock_check})
