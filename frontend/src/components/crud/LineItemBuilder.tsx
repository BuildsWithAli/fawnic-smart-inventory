import { Plus, Trash2 } from "lucide-react";
import { Select } from "../ui/Select";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import type { Product } from "../../types/models";
import { formatCurrency } from "../../utils/format";

export interface LineItem {
  product: string;
  quantity: string;
  price: string;
}

interface LineItemBuilderProps {
  items: LineItem[];
  products: Product[];
  priceLabel: string;
  onChange: (items: LineItem[]) => void;
}

export function LineItemBuilder({ items, products, priceLabel, onChange }: LineItemBuilderProps) {
  const update = (index: number, patch: Partial<LineItem>) => {
    onChange(items.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  };

  const addRow = () => onChange([...items, { product: "", quantity: "1", price: "" }]);
  const removeRow = (index: number) => onChange(items.filter((_, i) => i !== index));

  const total = items.reduce((sum, item) => {
    const qty = Number(item.quantity) || 0;
    const price = Number(item.price) || 0;
    return sum + qty * price;
  }, 0);

  return (
    <div className="flex flex-col gap-3">
      {items.map((item, index) => {
        const product = products.find((p) => String(p.id) === item.product);
        return (
          <div key={index} className="grid grid-cols-1 gap-2 rounded-lg border border-border p-3 sm:grid-cols-[1fr_90px_110px_auto]">
            <Select
              label={index === 0 ? "Product" : undefined}
              value={item.product}
              onChange={(e) => update(index, { product: e.target.value })}
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
              onChange={(e) => update(index, { quantity: e.target.value })}
            />
            <Input
              label={index === 0 ? priceLabel : undefined}
              type="number"
              step="0.01"
              min={0}
              value={item.price}
              onChange={(e) => update(index, { price: e.target.value })}
            />
            <div className="flex items-end justify-between gap-2">
              {product && (
                <span className="text-xs text-muted">
                  In stock: <span className="font-medium text-ink-soft">{product.quantity}</span>
                </span>
              )}
              <button
                type="button"
                onClick={() => removeRow(index)}
                className="ml-auto rounded-md p-2 text-muted hover:bg-danger-soft hover:text-danger"
                aria-label="Remove line item"
                disabled={items.length === 1}
              >
                <Trash2 size={15} />
              </button>
            </div>
          </div>
        );
      })}

      <div className="flex items-center justify-between">
        <Button type="button" variant="secondary" size="sm" onClick={addRow}>
          <Plus size={14} />
          Add line item
        </Button>
        <p className="text-sm font-medium text-ink">
          Total: <span className="font-display text-base">{formatCurrency(total)}</span>
        </p>
      </div>
    </div>
  );
}
