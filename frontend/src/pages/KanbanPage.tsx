import { useCallback, useEffect, useMemo, useState } from "react";
import { DragDropContext, Droppable, type DropResult } from "@hello-pangea/dnd";
import { Plus } from "lucide-react";
import clsx from "clsx";
import { Button } from "../components/ui/Button";
import { Select } from "../components/ui/Select";
import { Input } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { ErrorState } from "../components/ui/ErrorState";
import { Skeleton } from "../components/ui/Skeleton";
import { OrderCard } from "../features/kanban/OrderCard";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../hooks/useToast";
import { useAlertCount } from "../hooks/useAlertCount";
import { extractErrorMessage } from "../api/client";
import { orderApi, customerService, productService } from "../services";
import type { Customer, Order, OrderStatus, Product } from "../types/models";

// By default the Shipped column only shows orders that reached Shipped within this
// many days — older ones are archived out of the board view (nothing is deleted;
// "Show all shipped orders" brings them back). Keyed off the order's `shipped_at`.
const SHIPPED_BOARD_WINDOW_DAYS = 21;

const COLUMNS: { status: OrderStatus; label: string }[] = [
  { status: "pending", label: "Pending" },
  { status: "cutting", label: "Cutting" },
  { status: "stitching", label: "Stitching" },
  { status: "quality_check", label: "Quality Check" },
  { status: "shipped", label: "Shipped" },
];

interface NewOrderItem {
  product: string;
  quantity: string;
  unit_price: string;
}

export function KanbanPage() {
  const { show } = useToast();
  const { canWrite } = useAuth();
  const { refresh: refreshAlertCount } = useAlertCount();
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [customerId, setCustomerId] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [items, setItems] = useState<NewOrderItem[]>([{ product: "", quantity: "1", unit_price: "" }]);
  const [isSaving, setIsSaving] = useState(false);

  const [deletingOrder, setDeletingOrder] = useState<Order | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showAllShipped, setShowAllShipped] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params: Record<string, number> = { page_size: 200 };
      if (!showAllShipped) params.shipped_within_days = SHIPPED_BOARD_WINDOW_DAYS;
      const data = await orderApi.list(params);
      setOrders(data.results);
    } catch (err) {
      setError(extractErrorMessage(err, "Couldn't load orders."));
    } finally {
      setIsLoading(false);
    }
  }, [showAllShipped]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    void (async () => {
      const [customerData, productData] = await Promise.all([
        customerService.list({ page: 1 }),
        productService.list({ page: 1 }),
      ]);
      setCustomers(customerData.results);
      setProducts(productData.results);
    })();
  }, []);

  const columns = useMemo(() => {
    const grouped: Record<OrderStatus, Order[]> = {
      pending: [],
      cutting: [],
      stitching: [],
      quality_check: [],
      shipped: [],
    };
    for (const order of orders) grouped[order.status].push(order);
    return grouped;
  }, [orders]);

  const handleDragEnd = async (result: DropResult) => {
    if (!canWrite) return;
    const { destination, source, draggableId } = result;
    if (!destination) return;
    if (destination.droppableId === source.droppableId && destination.index === source.index) return;

    const newStatus = destination.droppableId as OrderStatus;
    const orderId = Number(draggableId);
    const previousOrders = orders;

    setOrders((prev) => prev.map((o) => (o.id === orderId ? { ...o, status: newStatus } : o)));

    try {
      const updated = await orderApi.updateStatus(orderId, newStatus);
      setOrders((prev) => prev.map((o) => (o.id === orderId ? updated : o)));

      const alertsBefore = previousOrders.find((o) => o.id === orderId)?.active_alerts_count ?? 0;
      if (updated.active_alerts_count > alertsBefore) {
        show(`Stock alert raised for order #${orderId} — see AI Alerts.`, "error");
      } else if (updated.ai_stock_check === "unavailable") {
        show("Order moved, but the AI stock check couldn't run just now.", "info");
      }
      // A new alert (or one resolved elsewhere) should show on the bell right away.
      refreshAlertCount();
    } catch (err) {
      setOrders(previousOrders);
      show(extractErrorMessage(err, "Couldn't move this order — it has been reverted."), "error");
    }
  };

  const openCreate = () => {
    setCustomerId("");
    setDueDate("");
    setItems([{ product: "", quantity: "1", unit_price: "" }]);
    setIsCreateOpen(true);
  };

  const isValid = useMemo(
    () => customerId && items.every((i) => i.product && Number(i.quantity) > 0 && Number(i.unit_price) > 0),
    [customerId, items],
  );

  const handleCreate = async () => {
    setIsSaving(true);
    try {
      await orderApi.create({
        customer: Number(customerId),
        due_date: dueDate || null,
        items_input: items.map((i) => ({
          product: Number(i.product),
          quantity: Number(i.quantity),
          unit_price: Number(i.unit_price),
        })),
      } as never);
      show("Order created.", "success");
      setIsCreateOpen(false);
      void load();
    } catch (err) {
      show(extractErrorMessage(err, "Couldn't create this order."), "error");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingOrder) return;
    setIsDeleting(true);
    try {
      await orderApi.remove(deletingOrder.id);
      show("Order deleted.", "success");
      setDeletingOrder(null);
      void load();
    } catch (err) {
      show(extractErrorMessage(err, "Couldn't delete this order."), "error");
    } finally {
      setIsDeleting(false);
    }
  };

  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <label className="flex cursor-pointer items-center gap-2 text-sm text-muted">
          <input
            type="checkbox"
            checked={showAllShipped}
            onChange={(e) => setShowAllShipped(e.target.checked)}
            className="h-4 w-4 rounded border-border text-accent focus:ring-2 focus:ring-accent/40"
          />
          Show all shipped orders
        </label>
        {canWrite && (
          <Button onClick={openCreate}>
            <Plus size={16} />
            New Order
          </Button>
        )}
      </div>

      <DragDropContext onDragEnd={handleDragEnd}>
        <div className="grid grid-cols-1 gap-4 overflow-x-auto pb-2 sm:grid-cols-2 xl:grid-cols-5">
          {COLUMNS.map((col) => (
            <Droppable key={col.status} droppableId={col.status}>
              {(provided, snapshot) => (
                <div
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  className={clsx(
                    "flex min-h-[420px] flex-col rounded-xl border border-border bg-surface-hover/60 p-3 transition-colors",
                    snapshot.isDraggingOver && "bg-accent-soft/50",
                  )}
                >
                  <div className="mb-3 px-1">
                    <div className="flex items-center justify-between">
                      <h3 className="font-display text-sm font-medium text-ink">{col.label}</h3>
                      <span className="rounded-full bg-surface px-2 py-0.5 text-xs text-muted border border-border">
                        {columns[col.status].length}
                      </span>
                    </div>
                    {col.status === "shipped" && !showAllShipped && (
                      <p className="mt-0.5 text-[11px] text-muted">Last {SHIPPED_BOARD_WINDOW_DAYS} days</p>
                    )}
                  </div>
                  <div className="flex flex-1 flex-col gap-2.5">
                    {isLoading ? (
                      <>
                        <Skeleton className="h-24 w-full" />
                        <Skeleton className="h-24 w-full" />
                      </>
                    ) : (
                      columns[col.status].map((order, index) => (
                        <OrderCard
                          key={order.id}
                          order={order}
                          index={index}
                          canDrag={canWrite}
                          canDelete={canWrite}
                          onDelete={setDeletingOrder}
                        />
                      ))
                    )}
                    {provided.placeholder}
                  </div>
                </div>
              )}
            </Droppable>
          ))}
        </div>
      </DragDropContext>

      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="New Order"
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)} disabled={isSaving}>
              Cancel
            </Button>
            <Button onClick={handleCreate} isLoading={isSaving} disabled={!isValid}>
              Create Order
            </Button>
          </>
        }
      >
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Select label="Customer" required value={customerId} onChange={(e) => setCustomerId(e.target.value)}>
              <option value="" disabled>
                Select customer
              </option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
            <Input label="Due Date" type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
          </div>

          <div className="flex flex-col gap-2">
            {items.map((item, index) => (
              <div key={index} className="grid grid-cols-[1fr_90px_110px] gap-2">
                <Select
                  label={index === 0 ? "Product" : undefined}
                  value={item.product}
                  onChange={(e) =>
                    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, product: e.target.value } : it)))
                  }
                >
                  <option value="" disabled>
                    Select product
                  </option>
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.sku})
                    </option>
                  ))}
                </Select>
                <Input
                  label={index === 0 ? "Qty" : undefined}
                  type="number"
                  min={1}
                  value={item.quantity}
                  onChange={(e) =>
                    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, quantity: e.target.value } : it)))
                  }
                />
                <Input
                  label={index === 0 ? "Unit Price" : undefined}
                  type="number"
                  min={0}
                  step="0.01"
                  value={item.unit_price}
                  onChange={(e) =>
                    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, unit_price: e.target.value } : it)))
                  }
                />
              </div>
            ))}
            <Button
              type="button"
              variant="secondary"
              size="sm"
              className="self-start"
              onClick={() => setItems((prev) => [...prev, { product: "", quantity: "1", unit_price: "" }])}
            >
              <Plus size={14} />
              Add product
            </Button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={deletingOrder !== null}
        title="Delete Order"
        message={
          deletingOrder && deletingOrder.active_alerts_count > 0
            ? `Are you sure you want to delete order #${deletingOrder.id}? This action cannot be undone. It has ${deletingOrder.active_alerts_count} unresolved stock alert(s) — they'll remain in Alert history but will no longer be linked to this order.`
            : "Are you sure you want to delete this order? This action cannot be undone."
        }
        confirmLabel="Delete"
        danger
        isLoading={isDeleting}
        onConfirm={handleDelete}
        onCancel={() => setDeletingOrder(null)}
      />
    </div>
  );
}
