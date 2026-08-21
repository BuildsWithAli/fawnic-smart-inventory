import { useEffect, useState } from "react";
import {
  Package,
  AlertTriangle,
  XCircle,
  Warehouse as WarehouseIcon,
  Tags,
  Truck,
  ShoppingCart,
  Receipt,
  DollarSign,
  Wallet,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import type { LucideIcon } from "lucide-react";
import { Card, CardHeader } from "../components/ui/Card";
import { Skeleton } from "../components/ui/Skeleton";
import { ErrorState } from "../components/ui/ErrorState";
import { StockStatusBadge, OrderStatusBadge, SaleStatusBadge } from "../components/crud/StatusBadge";
import { dashboardService } from "../services";
import type { DashboardData } from "../types/models";
import { formatCurrency, formatDate, formatShortDate } from "../utils/format";
import { extractErrorMessage } from "../api/client";

interface KpiSpec {
  key: keyof DashboardData["kpis"];
  label: string;
  icon: LucideIcon;
  format?: "currency" | "number";
}

const KPI_SPECS: KpiSpec[] = [
  { key: "total_products", label: "Total Products", icon: Package },
  { key: "low_stock", label: "Low Stock", icon: AlertTriangle },
  { key: "out_of_stock", label: "Out of Stock", icon: XCircle },
  { key: "warehouses", label: "Warehouses", icon: WarehouseIcon },
  { key: "categories", label: "Categories", icon: Tags },
  { key: "suppliers", label: "Suppliers", icon: Truck },
  { key: "purchase_orders", label: "Purchase Orders", icon: ShoppingCart },
  { key: "sales_orders", label: "Sales Orders", icon: Receipt },
  { key: "monthly_revenue", label: "Monthly Revenue", icon: DollarSign, format: "currency" },
  { key: "inventory_value", label: "Inventory Value", icon: Wallet, format: "currency" },
];

const STOCK_COLORS = { in_stock: "#3f7a5c", low_stock: "#b8790f", out_of_stock: "#b3403a" };

export function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const load = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await dashboardService.get();
      setData(result);
    } catch (err) {
      setError(extractErrorMessage(err, "Couldn't load the dashboard."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-5">
        {KPI_SPECS.map((spec) => (
          <KpiCard key={spec.key} spec={spec} data={data} isLoading={isLoading} />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader title="Sales vs Purchases" subtitle="Last 30 days" />
          <div className="h-72 px-2 pb-4">
            {isLoading || !data ? (
              <Skeleton className="h-full w-full" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.sales_vs_purchases} margin={{ top: 5, right: 12, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="salesGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#a9622c" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#a9622c" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="purchasesGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#3f7a5c" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#3f7a5c" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e7e1da" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tickFormatter={formatShortDate}
                    tick={{ fontSize: 11, fill: "#8a7f73" }}
                    axisLine={{ stroke: "#e7e1da" }}
                    tickLine={false}
                    interval={3}
                  />
                  <YAxis tick={{ fontSize: 11, fill: "#8a7f73" }} axisLine={false} tickLine={false} width={40} />
                  <Tooltip
                    formatter={(value) => formatCurrency(Number(value) || 0)}
                    labelFormatter={(label) => formatDate(label as string)}
                    contentStyle={{ borderRadius: 8, border: "1px solid #e7e1da", fontSize: 13 }}
                  />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Area type="monotone" dataKey="sales" name="Sales" stroke="#a9622c" fill="url(#salesGradient)" strokeWidth={2} />
                  <Area
                    type="monotone"
                    dataKey="purchases"
                    name="Purchases"
                    stroke="#3f7a5c"
                    fill="url(#purchasesGradient)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>

        <Card>
          <CardHeader title="Stock Health" subtitle="Current inventory breakdown" />
          <div className="h-72 px-2 pb-4">
            {isLoading || !data ? (
              <Skeleton className="h-full w-full" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={[
                      { name: "In Stock", value: data.stock_health.in_stock, key: "in_stock" },
                      { name: "Low Stock", value: data.stock_health.low_stock, key: "low_stock" },
                      { name: "Out of Stock", value: data.stock_health.out_of_stock, key: "out_of_stock" },
                    ]}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={62}
                    outerRadius={90}
                    paddingAngle={3}
                  >
                    {(["in_stock", "low_stock", "out_of_stock"] as const).map((key) => (
                      <Cell key={key} fill={STOCK_COLORS[key]} stroke="none" />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #e7e1da", fontSize: 13 }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader title="Recent Sales" />
          <div className="divide-y divide-border">
            {isLoading || !data ? (
              <div className="px-5 py-3 space-y-3">
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-full" />
              </div>
            ) : data.recent_sales.length === 0 ? (
              <p className="px-5 py-6 text-sm text-muted">No sales yet.</p>
            ) : (
              data.recent_sales.map((sale) => (
                <div key={sale.id} className="flex items-center justify-between gap-3 px-5 py-3 text-sm">
                  <div>
                    <p className="font-medium text-ink">
                      #{sale.id} · {sale.customer}
                    </p>
                    <p className="text-xs text-muted">{formatDate(sale.date)}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-ink-soft">{formatCurrency(sale.amount)}</span>
                    <SaleStatusBadge status={sale.status as never} />
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>

        <Card>
          <CardHeader title="Recent Purchases" />
          <div className="divide-y divide-border">
            {isLoading || !data ? (
              <div className="px-5 py-3 space-y-3">
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-full" />
              </div>
            ) : data.recent_purchases.length === 0 ? (
              <p className="px-5 py-6 text-sm text-muted">No purchases yet.</p>
            ) : (
              data.recent_purchases.map((purchase) => (
                <div key={purchase.id} className="flex items-center justify-between gap-3 px-5 py-3 text-sm">
                  <div>
                    <p className="font-medium text-ink">
                      #{purchase.id} · {purchase.supplier}
                    </p>
                    <p className="text-xs text-muted">{formatDate(purchase.date)}</p>
                  </div>
                  <span className="font-mono text-ink-soft">{formatCurrency(purchase.amount)}</span>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader title="Low Stock Products" subtitle="At or below reorder threshold" />
          <div className="divide-y divide-border">
            {isLoading || !data ? (
              <div className="px-5 py-3 space-y-3">
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-full" />
              </div>
            ) : data.low_stock_products.length === 0 ? (
              <p className="px-5 py-6 text-sm text-muted">Everything is well stocked.</p>
            ) : (
              data.low_stock_products.map((product) => (
                <div key={product.id} className="flex items-center justify-between gap-3 px-5 py-3 text-sm">
                  <div>
                    <p className="font-medium text-ink">{product.name}</p>
                    <p className="font-mono text-xs text-muted">{product.sku}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-ink-soft">
                      {product.quantity} / {product.reorder_threshold}
                    </span>
                    <StockStatusBadge status={product.stock_status} />
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>

        <Card>
          <CardHeader title="Recent Orders" subtitle="Production pipeline" />
          <div className="divide-y divide-border">
            {isLoading || !data ? (
              <div className="px-5 py-3 space-y-3">
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-5 w-full" />
              </div>
            ) : data.recent_orders.length === 0 ? (
              <p className="px-5 py-6 text-sm text-muted">No orders yet.</p>
            ) : (
              data.recent_orders.map((order) => (
                <div key={order.id} className="flex items-center justify-between gap-3 px-5 py-3 text-sm">
                  <div>
                    <p className="font-medium text-ink">
                      #{order.id} · {order.customer}
                    </p>
                    <p className="text-xs text-muted">Due {formatDate(order.due_date)}</p>
                  </div>
                  <OrderStatusBadge status={order.status} />
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}

function KpiCard({ spec, data, isLoading }: { spec: KpiSpec; data: DashboardData | null; isLoading: boolean }) {
  const value = data?.kpis[spec.key];
  return (
    <Card accent className="p-4">
      <div className="flex items-center gap-2 text-muted">
        <spec.icon size={15} />
        <span className="text-xs font-medium uppercase tracking-wide">{spec.label}</span>
      </div>
      {isLoading || value === undefined ? (
        <Skeleton className="mt-3 h-7 w-20" />
      ) : (
        <p className="mt-2 font-display text-2xl font-medium text-ink">
          {spec.format === "currency" ? formatCurrency(value) : value.toLocaleString()}
        </p>
      )}
    </Card>
  );
}
