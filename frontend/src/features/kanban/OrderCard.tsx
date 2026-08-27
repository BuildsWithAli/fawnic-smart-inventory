import { Draggable } from "@hello-pangea/dnd";
import { AlertTriangle, CalendarDays, Trash2 } from "lucide-react";
import clsx from "clsx";
import type { Order } from "../../types/models";
import { formatDate } from "../../utils/format";

export function OrderCard({
  order,
  index,
  canDrag = true,
  canDelete = false,
  onDelete,
}: {
  order: Order;
  index: number;
  canDrag?: boolean;
  canDelete?: boolean;
  onDelete?: (order: Order) => void;
}) {
  const hasStockRisk = order.items.some((item) => item.stock_status !== "in_stock");
  const isLockedToSale = order.generated_sale !== null;

  return (
    <Draggable draggableId={String(order.id)} index={index} isDragDisabled={!canDrag}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          className={clsx(
            "group select-none rounded-lg border border-border bg-surface p-3.5 shadow-sm transition-shadow",
            canDrag && "cursor-grab active:cursor-grabbing",
            snapshot.isDragging && "shadow-lg ring-2 ring-accent/30",
          )}
        >
          <div className="mb-2 flex items-start justify-between gap-2">
            <span className="font-mono text-xs text-muted">#{order.id}</span>
            <div className="flex items-center gap-1.5">
              {(order.active_alerts_count > 0 || hasStockRisk) && (
                <span className="flex items-center gap-1 rounded-full bg-danger-soft px-2 py-0.5 text-[11px] font-medium text-danger">
                  <AlertTriangle size={11} />
                  {order.active_alerts_count > 0 ? order.active_alerts_count : "Risk"}
                </span>
              )}
              {canDelete && (
                <button
                  type="button"
                  onClick={() => onDelete?.(order)}
                  disabled={isLockedToSale}
                  aria-label="Delete order"
                  title={isLockedToSale ? "This order already produced a sale and can't be deleted." : "Delete order"}
                  className={clsx(
                    "rounded-md p-1 text-muted opacity-0 transition-opacity group-hover:opacity-100",
                    isLockedToSale ? "cursor-not-allowed opacity-40 group-hover:opacity-40" : "hover:bg-danger-soft hover:text-danger",
                  )}
                >
                  <Trash2 size={13} />
                </button>
              )}
            </div>
          </div>
          <p className="text-sm font-medium text-ink">{order.customer_name}</p>
          <ul className="mt-1.5 space-y-0.5">
            {order.items.slice(0, 3).map((item) => (
              <li key={item.id} className="truncate text-xs text-muted">
                {item.quantity}× {item.product_name}
              </li>
            ))}
            {order.items.length > 3 && <li className="text-xs text-muted">+{order.items.length - 3} more</li>}
          </ul>
          {order.due_date && (
            <div className="mt-2.5 flex items-center gap-1.5 text-xs text-muted">
              <CalendarDays size={12} />
              Due {formatDate(order.due_date)}
            </div>
          )}
        </div>
      )}
    </Draggable>
  );
}
