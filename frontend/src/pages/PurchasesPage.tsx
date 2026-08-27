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
import { LineItemBuilder, type LineItem } from "../components/crud/LineItemBuilder";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../hooks/useToast";
import { extractErrorMessage } from "../api/client";
import { purchaseService, supplierService, productService } from "../services";
import type { Product, Purchase, Supplier } from "../types/models";
import { formatCurrency, formatDate } from "../utils/format";

const PAGE_SIZE = 20;

export function PurchasesPage() {
  const { show } = useToast();
  const { canWrite } = useAuth();
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [products, setProducts] = useState<Product[]>([]);

  const [rows, setRows] = useState<Purchase[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [supplierId, setSupplierId] = useState("");
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [items, setItems] = useState<LineItem[]>([{ product: "", quantity: "1", price: "" }]);
  const [isSaving, setIsSaving] = useState(false);

  const [viewing, setViewing] = useState<Purchase | null>(null);
  const [deleting, setDeleting] = useState<Purchase | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    void (async () => {
      const [supplierData, productData] = await Promise.all([
        supplierService.list({ page: 1 }),
        productService.list({ page: 1 }),
      ]);
      setSuppliers(supplierData.results);
      setProducts(productData.results);
    })();
  }, []);

  const load = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await purchaseService.list({ page });
      setRows(data.results);
      setCount(data.count);
    } catch (err) {
      setError(extractErrorMessage(err, "Couldn't load purchases."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const openCreate = () => {
    setSupplierId("");
    setDate(new Date().toISOString().slice(0, 10));
    setItems([{ product: "", quantity: "1", price: "" }]);
    setIsCreateOpen(true);
  };

  const isValid = useMemo(
    () => supplierId && items.every((i) => i.product && Number(i.quantity) > 0 && Number(i.price) >= 0),
    [supplierId, items],
  );

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await purchaseService.create({
        supplier: Number(supplierId),
        date,
        items_input: items.map((i) => ({
          product: Number(i.product),
          quantity: Number(i.quantity),
          unit_cost: Number(i.price),
        })),
      } as never);
      show("Purchase recorded — inventory updated.", "success");
      setIsCreateOpen(false);
      void load();
      const productData = await productService.list({ page: 1 });
      setProducts(productData.results);
    } catch (err) {
      show(extractErrorMessage(err, "Couldn't save this purchase."), "error");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleting) return;
    setIsDeleting(true);
    try {
      await purchaseService.remove(deleting.id);
      show("Purchase deleted.", "success");
      setDeleting(null);
      void load();
    } catch (err) {
      show(extractErrorMessage(err, "Couldn't delete this purchase."), "error");
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
            New Purchase
          </Button>
        </div>
      )}

      <Card className="overflow-hidden">
        <DataTable
          columns={[
            { key: "id", header: "Purchase", render: (row) => <span className="font-medium text-ink">#{row.id}</span> },
            { key: "supplier_name", header: "Supplier", render: (row) => row.supplier_name },
            { key: "date", header: "Date", render: (row) => formatDate(row.date) },
            { key: "items", header: "Items", render: (row) => row.items.length },
            { key: "total", header: "Total", render: (row) => formatCurrency(row.total) },
          ]}
          rows={rows}
          rowKey={(row) => row.id}
          isLoading={isLoading}
          error={error}
          onRetry={load}
          emptyTitle="No purchases found"
          emptyDescription="Record your first purchase to bring materials or products into stock."
          rowActions={(row) => (
            <div className="flex items-center justify-end gap-1">
              <button
                onClick={() => setViewing(row)}
                className="rounded-md p-1.5 text-muted hover:bg-surface-hover hover:text-ink"
                aria-label="View purchase"
              >
                <Eye size={15} />
              </button>
              {canWrite && (
                <button
                  onClick={() => setDeleting(row)}
                  className="rounded-md p-1.5 text-muted hover:bg-danger-soft hover:text-danger"
                  aria-label="Delete purchase"
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
        title="New Purchase"
        subtitle="Recording a purchase automatically increases stock for each line item."
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)} disabled={isSaving}>
              Cancel
            </Button>
            <Button onClick={handleSave} isLoading={isSaving} disabled={!isValid}>
              Save Purchase
            </Button>
          </>
        }
      >
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Select label="Supplier" required value={supplierId} onChange={(e) => setSupplierId(e.target.value)}>
              <option value="" disabled>
                Select supplier
              </option>
              {suppliers.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </Select>
            <Input label="Date" type="date" required value={date} onChange={(e) => setDate(e.target.value)} />
          </div>
          <LineItemBuilder items={items} products={products} priceLabel="Unit Cost" onChange={setItems} />
        </div>
      </Modal>

      <Modal
        isOpen={viewing !== null}
        onClose={() => setViewing(null)}
        title={viewing ? `Purchase #${viewing.id}` : ""}
        subtitle={viewing ? `${viewing.supplier_name} · ${formatDate(viewing.date)}` : undefined}
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
                  {item.quantity} × {formatCurrency(item.unit_cost)} = {formatCurrency(item.line_total)}
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
        title="Delete Purchase"
        message="Deleting this purchase will reverse the stock it added, in the same step. If some of that stock has since been sold, the deletion will be blocked. This can't be undone."
        confirmLabel="Delete"
        danger
        isLoading={isDeleting}
        onConfirm={handleDelete}
        onCancel={() => setDeleting(null)}
      />
    </div>
  );
}
