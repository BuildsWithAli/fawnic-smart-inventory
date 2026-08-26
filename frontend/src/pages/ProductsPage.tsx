import { useEffect, useMemo, useState } from "react";
import { Plus, Pencil, Trash2, SlidersHorizontal } from "lucide-react";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Select } from "../components/ui/Select";
import { DataTable } from "../components/crud/DataTable";
import { SearchBar } from "../components/crud/SearchBar";
import { FilterBar } from "../components/crud/FilterBar";
import { Modal } from "../components/ui/Modal";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { Pagination } from "../components/ui/Pagination";
import { StockStatusBadge } from "../components/crud/StatusBadge";
import { useDebounce } from "../hooks/useDebounce";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../hooks/useToast";
import { extractErrorMessage } from "../api/client";
import { productService, brandService, categoryService, warehouseService, stockAdjustmentApi } from "../services";
import type { Brand, Category, Product, Warehouse } from "../types/models";
import { formatCurrency } from "../utils/format";

const PAGE_SIZE = 20;

interface ProductFormValues {
  sku: string;
  name: string;
  category: string;
  brand: string;
  warehouse: string;
  quantity: string;
  unit_cost: string;
  reorder_threshold: string;
}

const EMPTY_FORM: ProductFormValues = {
  sku: "",
  name: "",
  category: "",
  brand: "",
  warehouse: "",
  quantity: "0",
  unit_cost: "",
  reorder_threshold: "10",
};

export function ProductsPage() {
  const { show } = useToast();
  const { canWrite } = useAuth();
  const [categories, setCategories] = useState<Category[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);

  const [rows, setRows] = useState<Product[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search);
  const [filterValues, setFilterValues] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editingProduct, setEditingProduct] = useState<Product | "new" | null>(null);
  const [formValues, setFormValues] = useState<ProductFormValues>(EMPTY_FORM);
  const [isSaving, setIsSaving] = useState(false);

  const [adjustingProduct, setAdjustingProduct] = useState<Product | null>(null);
  const [newQuantity, setNewQuantity] = useState("");
  const [reason, setReason] = useState("");
  const [isAdjusting, setIsAdjusting] = useState(false);

  const [deletingProduct, setDeletingProduct] = useState<Product | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    void (async () => {
      const [cats, brds, whs] = await Promise.all([
        categoryService.list({ page: 1 }),
        brandService.list({ page: 1 }),
        warehouseService.list({ page: 1 }),
      ]);
      setCategories(cats.results);
      setBrands(brds.results);
      setWarehouses(whs.results);
    })();
  }, []);

  const filters = useMemo(
    () => [
      { key: "category", label: "Category", options: categories.map((c) => ({ value: String(c.id), label: c.name })) },
      { key: "brand", label: "Brand", options: brands.map((b) => ({ value: String(b.id), label: b.name })) },
      { key: "warehouse", label: "Warehouse", options: warehouses.map((w) => ({ value: String(w.id), label: w.name })) },
    ],
    [categories, brands, warehouses],
  );

  const params = useMemo(
    () => ({ search: debouncedSearch || undefined, page, ...filterValues }),
    [debouncedSearch, page, filterValues],
  );

  const load = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await productService.list(params);
      setRows(data.results);
      setCount(data.count);
    } catch (err) {
      setError(extractErrorMessage(err, "Couldn't load products."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(params)]);

  const openCreate = () => {
    setFormValues(EMPTY_FORM);
    setEditingProduct("new");
  };

  const openEdit = (product: Product) => {
    setFormValues({
      sku: product.sku,
      name: product.name,
      category: String(product.category),
      brand: String(product.brand),
      warehouse: String(product.warehouse),
      quantity: String(product.quantity),
      unit_cost: product.unit_cost,
      reorder_threshold: String(product.reorder_threshold),
    });
    setEditingProduct(product);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const payload = {
        sku: formValues.sku,
        name: formValues.name,
        category: Number(formValues.category),
        brand: Number(formValues.brand),
        warehouse: Number(formValues.warehouse),
        unit_cost: formValues.unit_cost,
        reorder_threshold: Number(formValues.reorder_threshold),
        ...(editingProduct === "new" ? { quantity: Number(formValues.quantity) } : {}),
      };
      if (editingProduct === "new") {
        await productService.create(payload);
        show("Product created.", "success");
      } else if (editingProduct) {
        await productService.update(editingProduct.id, payload);
        show("Product updated.", "success");
      }
      setEditingProduct(null);
      void load();
    } catch (err) {
      show(extractErrorMessage(err, "Couldn't save this product."), "error");
    } finally {
      setIsSaving(false);
    }
  };

  const openAdjust = (product: Product) => {
    setAdjustingProduct(product);
    setNewQuantity(String(product.quantity));
    setReason("");
  };

  const handleAdjust = async () => {
    if (!adjustingProduct) return;
    setIsAdjusting(true);
    try {
      await stockAdjustmentApi.adjust(adjustingProduct.id, {
        new_quantity: Number(newQuantity),
        reason,
      });
      show("Stock adjusted.", "success");
      setAdjustingProduct(null);
      void load();
    } catch (err) {
      show(extractErrorMessage(err, "Couldn't adjust stock."), "error");
    } finally {
      setIsAdjusting(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingProduct) return;
    setIsDeleting(true);
    try {
      await productService.remove(deletingProduct.id);
      show("Product deleted.", "success");
      setDeletingProduct(null);
      void load();
    } catch (err) {
      show(extractErrorMessage(err, "Couldn't delete this product."), "error");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <SearchBar
            value={search}
            onChange={(v) => {
              setPage(1);
              setSearch(v);
            }}
            placeholder="Search by name or SKU..."
          />
          <FilterBar
            filters={filters}
            values={filterValues}
            onChange={(key, value) => {
              setPage(1);
              setFilterValues((prev) => ({ ...prev, [key]: value }));
            }}
          />
        </div>
        {canWrite && (
          <Button onClick={openCreate}>
            <Plus size={16} />
            Add Product
          </Button>
        )}
      </div>

      <Card className="overflow-hidden">
        <DataTable
          columns={[
            {
              key: "name",
              header: "Product",
              render: (row) => (
                <div>
                  <p className="font-medium text-ink">{row.name}</p>
                  <p className="font-mono text-xs text-muted">{row.sku}</p>
                </div>
              ),
            },
            { key: "category", header: "Category", render: (row) => row.category_name },
            { key: "brand", header: "Brand", render: (row) => row.brand_name },
            { key: "warehouse", header: "Warehouse", render: (row) => row.warehouse_name },
            { key: "quantity", header: "Quantity", render: (row) => row.quantity },
            { key: "unit_cost", header: "Unit Cost", render: (row) => formatCurrency(row.unit_cost) },
            { key: "reorder_threshold", header: "Reorder At", render: (row) => row.reorder_threshold },
            { key: "stock_status", header: "Status", render: (row) => <StockStatusBadge status={row.stock_status} /> },
          ]}
          rows={rows}
          rowKey={(row) => row.id}
          isLoading={isLoading}
          error={error}
          onRetry={load}
          emptyTitle="No products found"
          emptyDescription="Add your first product to start managing inventory."
          rowActions={
            canWrite
              ? (row) => (
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => openAdjust(row)}
                      className="rounded-md p-1.5 text-muted hover:bg-surface-hover hover:text-ink"
                      aria-label="Adjust stock"
                      title="Adjust stock"
                    >
                      <SlidersHorizontal size={15} />
                    </button>
                    <button
                      onClick={() => openEdit(row)}
                      className="rounded-md p-1.5 text-muted hover:bg-surface-hover hover:text-ink"
                      aria-label="Edit product"
                    >
                      <Pencil size={15} />
                    </button>
                    <button
                      onClick={() => setDeletingProduct(row)}
                      className="rounded-md p-1.5 text-muted hover:bg-danger-soft hover:text-danger"
                      aria-label="Delete product"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                )
              : undefined
          }
        />
        {!isLoading && !error && rows.length > 0 && (
          <Pagination page={page} pageSize={PAGE_SIZE} total={count} onPageChange={setPage} />
        )}
      </Card>

      <Modal
        isOpen={editingProduct !== null}
        onClose={() => setEditingProduct(null)}
        title={editingProduct === "new" ? "Add Product" : "Edit Product"}
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditingProduct(null)} disabled={isSaving}>
              Cancel
            </Button>
            <Button onClick={handleSave} isLoading={isSaving}>
              Save
            </Button>
          </>
        }
      >
        <form className="grid grid-cols-1 gap-4 sm:grid-cols-2" onSubmit={(e) => e.preventDefault()}>
          <Input
            label="SKU"
            required
            value={formValues.sku}
            onChange={(e) => setFormValues((v) => ({ ...v, sku: e.target.value }))}
          />
          <Input
            label="Name"
            required
            value={formValues.name}
            onChange={(e) => setFormValues((v) => ({ ...v, name: e.target.value }))}
          />
          <Select
            label="Category"
            required
            value={formValues.category}
            onChange={(e) => setFormValues((v) => ({ ...v, category: e.target.value }))}
          >
            <option value="" disabled>
              Select category
            </option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
          <Select
            label="Brand"
            required
            value={formValues.brand}
            onChange={(e) => setFormValues((v) => ({ ...v, brand: e.target.value }))}
          >
            <option value="" disabled>
              Select brand
            </option>
            {brands.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </Select>
          <Select
            label="Warehouse"
            required
            value={formValues.warehouse}
            onChange={(e) => setFormValues((v) => ({ ...v, warehouse: e.target.value }))}
          >
            <option value="" disabled>
              Select warehouse
            </option>
            {warehouses.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </Select>
          <Input
            label="Unit Cost"
            type="number"
            step="0.01"
            min={0}
            required
            value={formValues.unit_cost}
            onChange={(e) => setFormValues((v) => ({ ...v, unit_cost: e.target.value }))}
          />
          <Input
            label="Reorder Threshold"
            type="number"
            min={0}
            required
            value={formValues.reorder_threshold}
            onChange={(e) => setFormValues((v) => ({ ...v, reorder_threshold: e.target.value }))}
          />
          {editingProduct === "new" && (
            <Input
              label="Starting Quantity"
              type="number"
              min={0}
              value={formValues.quantity}
              onChange={(e) => setFormValues((v) => ({ ...v, quantity: e.target.value }))}
              hint="Record purchases afterwards to increase stock further."
            />
          )}
        </form>
      </Modal>

      <Modal
        isOpen={adjustingProduct !== null}
        onClose={() => setAdjustingProduct(null)}
        title="Adjust Stock"
        subtitle={adjustingProduct ? `${adjustingProduct.name} · ${adjustingProduct.sku}` : undefined}
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setAdjustingProduct(null)} disabled={isAdjusting}>
              Cancel
            </Button>
            <Button onClick={handleAdjust} isLoading={isAdjusting} disabled={!reason.trim()}>
              Apply Adjustment
            </Button>
          </>
        }
      >
        <div className="flex flex-col gap-4">
          <p className="text-sm text-muted">
            Current quantity: <span className="font-medium text-ink">{adjustingProduct?.quantity}</span>
          </p>
          <Input
            label="New Quantity"
            type="number"
            min={0}
            value={newQuantity}
            onChange={(e) => setNewQuantity(e.target.value)}
          />
          <Input
            label="Reason"
            placeholder="e.g. Damaged goods, stock count correction..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            required
          />
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={deletingProduct !== null}
        title="Delete Product"
        message="Are you sure you want to delete this product? This action cannot be undone."
        confirmLabel="Delete"
        danger
        isLoading={isDeleting}
        onConfirm={handleDelete}
        onCancel={() => setDeletingProduct(null)}
      />
    </div>
  );
}
