import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
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

    def get_queryset(self):
        """Optional `?shipped_within_days=N` trims the Shipped column of the Kanban board.

        Orders in every other status are returned untouched. A shipped order is kept
        only if its `shipped_at` falls within the last N days; a shipped order with a
        null `shipped_at` (legacy data) is treated as outside any window. This is a
        display filter for the board fetch only — no row is modified or deleted, and
        callers that omit the parameter (Orders list, dashboard, exports) are unaffected.
        """
        queryset = super().get_queryset()
        raw = self.request.query_params.get("shipped_within_days")
        # Only ever narrows the board listing — never detail lookups or the
        # status-change action, so an archived order stays reachable by id.
        if self.action != "list" or raw in (None, ""):
            return queryset
        try:
            days = int(raw)
        except (TypeError, ValueError):
            raise ValidationError({"shipped_within_days": "Must be a whole number of days."})
        if days < 0:
            raise ValidationError({"shipped_within_days": "Must be zero or a positive number of days."})
        cutoff = timezone.now() - timedelta(days=days)
        return queryset.filter(~Q(status=Order.Status.SHIPPED) | Q(shipped_at__gte=cutoff))

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
            entering_shipped = (
                new_status == Order.Status.SHIPPED and previous_status != Order.Status.SHIPPED
            )
            order.status = new_status
            update_fields = ["status", "updated_at"]
            if entering_shipped:
                order.shipped_at = timezone.now()
                update_fields.append("shipped_at")
            order.save(update_fields=update_fields)

            if entering_shipped and order.generated_sale_id is None:
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
