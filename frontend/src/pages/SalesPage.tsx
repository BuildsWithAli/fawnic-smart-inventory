import { useEffect, useMemo, useState } from "react";
import { Plus, Eye, Trash2 } from "lucide-react";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Select } from "../components/ui/Select";
import { DataTable } from "../components/crud/DataTable";
import { Modal } from "../components/ui/Modal";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { Pagination } from "../components/ui/Pagination";
import { SaleStatusBadge } from "../components/crud/StatusBadge";
import { LineItemBuilder, type LineItem } from "../components/crud/LineItemBuilder";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../hooks/useToast";
import { extractErrorMessage } from "../api/client";
import { saleService, customerService, productService } from "../services";
import type { Customer, Product, Sale } from "../types/models";
import { formatCurrency, formatDate } from "../utils/format";

const PAGE_SIZE = 20;

export function SalesPage() {
  const { show } = useToast();
  const { canWrite } = useAuth();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [products, setProducts] = useState<Product[]>([]);

  const [rows, setRows] = useState<Sale[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [customerId, setCustomerId] = useState("");
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [items, setItems] = useState<LineItem[]>([{ product: "", quantity: "1", price: "" }]);
  const [isSaving, setIsSaving] = useState(false);

  const [viewing, setViewing] = useState<Sale | null>(null);
  const [deleting, setDeleting] = useState<Sale | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

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

  const load = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await saleService.list({ page });
      setRows(data.results);
      setCount(data.count);
    } catch (err) {
      setError(extractErrorMessage(err, "Couldn't load sales."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const openCreate = () => {
    setCustomerId("");
    setDate(new Date().toISOString().slice(0, 10));
    setItems([{ product: "", quantity: "1", price: "" }]);
    setIsCreateOpen(true);
  };

  const isValid = useMemo(
    () => customerId && items.every((i) => i.product && Number(i.quantity) > 0 && Number(i.price) >= 0),
    [customerId, items],
  );

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await saleService.create({
        customer: Number(customerId),
        date,
        items_input: items.map((i) => ({
          product: Number(i.product),
          quantity: Number(i.quantity),
          unit_price: Number(i.price),
        })),
      } as never);
      show("Sale recorded — inventory updated.", "success");
      setIsCreateOpen(false);
      void load();
      const productData = await productService.list({ page: 1 });
      setProducts(productData.results);
    } catch (err) {
      show(extractErrorMessage(err, "Couldn't save this sale — check that enough stock is available."), "error");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleting) return;
    setIsDeleting(true);
    try {
      await saleService.remove(deleting.id);
      show("Sale deleted.", "success");
      setDeleting(null);
      void load();
    } catch (err) {
      show(extractErrorMessage(err, "Couldn't delete this sale."), "error");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      {canWrite && (
        <div className="flex justify-end">
          <Button onClick={openCreate}>
            <Plus size={16} />
            New Sale
          </Button>
        </div>
      )}

      <Card className="overflow-hidden">
        <DataTable
          columns={[
            { key: "id", header: "Sale", render: (row) => <span className="font-medium text-ink">#{row.id}</span> },
            { key: "customer_name", header: "Customer", render: (row) => row.customer_name },
            { key: "date", header: "Date", render: (row) => formatDate(row.date) },
            { key: "items", header: "Items", render: (row) => row.items.length },
            { key: "total", header: "Total", render: (row) => formatCurrency(row.total) },
            { key: "status", header: "Status", render: (row) => <SaleStatusBadge status={row.status} /> },
          ]}
          rows={rows}
          rowKey={(row) => row.id}
          isLoading={isLoading}
          error={error}
          onRetry={load}
          emptyTitle="No sales found"
          emptyDescription="Record your first sale to see it reflected in inventory."
          rowActions={(row) => (
            <div className="flex items-center justify-end gap-1">
              <button
                onClick={() => setViewing(row)}
                className="rounded-md p-1.5 text-muted hover:bg-surface-hover hover:text-ink"
                aria-label="View sale"
              >
                <Eye size={15} />
              </button>
              {canWrite && (
                <button
                  onClick={() => setDeleting(row)}
                  className="rounded-md p-1.5 text-muted hover:bg-danger-soft hover:text-danger"
                  aria-label="Delete sale"
                >
                  <Trash2 size={15} />
                </button>
              )}
            </div>
          )}
        />
        {!isLoading && !error && rows.length > 0 && (
          <Pagination page={page} pageSize={PAGE_SIZE} total={count} onPageChange={setPage} />
        )}
      </Card>

      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="New Sale"
        subtitle="Recording a sale automatically decreases stock for each line item."
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)} disabled={isSaving}>
              Cancel
            </Button>
            <Button onClick={handleSave} isLoading={isSaving} disabled={!isValid}>
              Save Sale
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
            <Input label="Date" type="date" required value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
          <LineItemBuilder items={items} products={products} priceLabel="Unit Price" onChange={setItems} />
        </div>
      </Modal>

      <Modal
        isOpen={viewing !== null}
        onClose={() => setViewing(null)}
        title={viewing ? `Sale #${viewing.id}` : ""}
        subtitle={viewing ? `${viewing.customer_name} · ${formatDate(viewing.date)}` : undefined}
      >
        {viewing && (
          <div className="divide-y divide-border">
            {viewing.items.map((item) => (
              <div key={item.id} className="flex items-center justify-between py-2.5 text-sm">
                <div>
                  <p className="font-medium text-ink">{item.product_name}</p>
                  <p className="font-mono text-xs text-muted">{item.sku}</p>
                </div>
                <p className="text-ink-soft">
                  {item.quantity} × {formatCurrency(item.unit_price)} = {formatCurrency(item.line_total)}
                </p>
              </div>
            ))}
            <div className="flex justify-between pt-3 text-sm font-medium text-ink">
              <span>Total</span>
              <span>{formatCurrency(viewing.total)}</span>
            </div>
          </div>
        )}
      </Modal>

      <ConfirmDialog
        isOpen={deleting !== null}
        title="Delete Sale"
        message="Deleting this sale will restore the stock it deducted back to each product, in the same step. This can't be undone."
        confirmLabel="Delete"
        danger
        isLoading={isDeleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleting(null)}
      />
    </div>
  );
}
