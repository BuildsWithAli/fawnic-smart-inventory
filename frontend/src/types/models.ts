export type Role = "owner" | "inventory_manager" | "support";

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Brand {
  id: number;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: number;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface Warehouse {
  id: number;
  name: string;
  location: string;
  capacity_notes: string;
  created_at: string;
  updated_at: string;
}

export type StockStatus = "in_stock" | "low_stock" | "out_of_stock";

export interface Product {
  id: number;
  sku: string;
  name: string;
  category: number;
  category_name: string;
  brand: number;
  brand_name: string;
  warehouse: number;
  warehouse_name: string;
  quantity: number;
  unit_cost: string;
  reorder_threshold: number;
  stock_status: StockStatus;
  inventory_value: string;
  created_at: string;
  updated_at: string;
}

export interface StockAdjustment {
  id: number;
  product: number;
  product_name: string;
  sku: string;
  previous_quantity: number;
  new_quantity: number;
  difference: number;
  reason: string;
  user: number | null;
  user_name: string | null;
  created_at: string;
}

export interface Supplier {
  id: number;
  name: string;
  contact_name: string;
  email: string;
  phone: string;
  address: string;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: number;
  name: string;
  email: string;
  phone: string;
  address: string;
  created_at: string;
  updated_at: string;
}

export interface PurchaseItem {
  id: number;
  product: number;
  product_name: string;
  sku: string;
  quantity: number;
  unit_cost: string;
  line_total: string;
}

export interface Purchase {
  id: number;
  supplier: number;
  supplier_name: string;
  date: string;
  items: PurchaseItem[];
  items_input?: { product: number; quantity: number; unit_cost: number }[];
  total: string;
  created_at: string;
}

export interface SaleItem {
  id: number;
  product: number;
  product_name: string;
  sku: string;
  quantity: number;
  unit_price: string;
  line_total: string;
}

export type SaleStatus = "completed" | "refunded" | "cancelled";

export interface Sale {
  id: number;
  customer: number;
  customer_name: string;
  date: string;
  status: SaleStatus;
  items: SaleItem[];
  items_input?: { product: number; quantity: number; unit_price: number }[];
  total: string;
  created_at: string;
}

export type OrderStatus = "pending" | "cutting" | "stitching" | "quality_check" | "shipped";

export interface OrderItem {
  id: number;
  product: number;
  product_name: string;
  sku: string;
  quantity: number;
  unit_price: string;
  stock_status: StockStatus;
}

export interface Order {
  id: number;
  customer: number;
  customer_name: string;
  items: OrderItem[];
  items_input?: { product: number; quantity: number; unit_price: number }[];
  status: OrderStatus;
  due_date: string | null;
  // Set when the order last transitioned into "shipped"; null for orders that
  // have never shipped (and for legacy shipped orders created before this field).
  shipped_at: string | null;
  active_alerts_count: number;
  generated_sale: number | null;
  created_at: string;
  updated_at: string;
}

// Result of the AI stock-check the backend runs on an order status change:
//   "ok"          — a provider completed the check (alerts may or may not have been raised)
//   "skipped"     — the order has no line items, nothing to check
//   "unavailable" — every AI provider rung failed/timed out; no check ran
export type AiStockCheckStatus = "ok" | "skipped" | "unavailable";

export interface OrderStatusUpdateResult extends Order {
  ai_stock_check: AiStockCheckStatus;
}

export type AlertSeverity = "low" | "medium" | "high" | "critical";

export interface StockAlert {
  id: number;
  product: number;
  product_name: string;
  sku: string;
  order: number | null;
  order_status: string | null;
  severity: AlertSeverity;
  current_stock_at_alert: number;
  reorder_threshold_at_alert: number;
  suggested_quantity: number | null;
  resolved: boolean;
  created_at: string;
}

export interface DashboardKpis {
  total_products: number;
  low_stock: number;
  out_of_stock: number;
  warehouses: number;
  categories: number;
  brands: number;
  suppliers: number;
  purchase_orders: number;
  sales_orders: number;
  monthly_revenue: number;
  inventory_value: number;
}

export interface SalesVsPurchasesPoint {
  date: string;
  sales: number;
  purchases: number;
}

export interface StockHealth {
  in_stock: number;
  low_stock: number;
  out_of_stock: number;
}

export interface RecentSale {
  id: number;
  customer: string;
  amount: number;
  date: string;
  status: string;
}

export interface RecentPurchase {
  id: number;
  supplier: string;
  amount: number;
  date: string;
}

export interface LowStockProduct {
  id: number;
  name: string;
  sku: string;
  quantity: number;
  reorder_threshold: number;
  stock_status: StockStatus;
}

export interface RecentOrder {
  id: number;
  customer: string;
  status: OrderStatus;
  due_date: string | null;
}

export interface DashboardData {
  kpis: DashboardKpis;
  sales_vs_purchases: SalesVsPurchasesPoint[];
  stock_health: StockHealth;
  recent_sales: RecentSale[];
  recent_purchases: RecentPurchase[];
  low_stock_products: LowStockProduct[];
  recent_orders: RecentOrder[];
}
