import { Badge } from "../ui/Badge";
import type { StockStatus, OrderStatus, AlertSeverity, SaleStatus } from "../../types/models";

const STOCK_LABELS: Record<StockStatus, string> = {
  in_stock: "In Stock",
  low_stock: "Low Stock",
  out_of_stock: "Out of Stock",
};

export function StockStatusBadge({ status }: { status: StockStatus }) {
  const tone = status === "in_stock" ? "success" : status === "low_stock" ? "warning" : "danger";
  return <Badge tone={tone}>{STOCK_LABELS[status]}</Badge>;
}

const ORDER_LABELS: Record<OrderStatus, string> = {
  pending: "Pending",
  cutting: "Cutting",
  stitching: "Stitching",
  quality_check: "Quality Check",
  shipped: "Shipped",
};

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  const tone = status === "shipped" ? "success" : status === "pending" ? "neutral" : "accent";
  return <Badge tone={tone}>{ORDER_LABELS[status]}</Badge>;
}

const SEVERITY_TONE: Record<AlertSeverity, "neutral" | "warning" | "danger"> = {
  low: "neutral",
  medium: "warning",
  high: "warning",
  critical: "danger",
};

export function SeverityBadge({ severity }: { severity: AlertSeverity }) {
  return <Badge tone={SEVERITY_TONE[severity]}>{severity[0].toUpperCase() + severity.slice(1)}</Badge>;
}

const SALE_STATUS_TONE: Record<SaleStatus, "success" | "warning" | "danger"> = {
  completed: "success",
  refunded: "warning",
  cancelled: "danger",
};

export function SaleStatusBadge({ status }: { status: SaleStatus }) {
  return <Badge tone={SALE_STATUS_TONE[status]}>{status[0].toUpperCase() + status.slice(1)}</Badge>;
}
