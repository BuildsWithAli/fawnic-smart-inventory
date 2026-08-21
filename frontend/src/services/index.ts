import { apiClient } from "../api/client";
import { createResourceService } from "./resource";
import type {
  Brand,
  Category,
  Customer,
  DashboardData,
  Order,
  Product,
  Purchase,
  Sale,
  StockAdjustment,
  StockAlert,
  Supplier,
  Warehouse,
} from "../types/models";

export const brandService = createResourceService<Brand>("brands");
export const categoryService = createResourceService<Category>("categories");
export const warehouseService = createResourceService<Warehouse>("warehouses");
export const supplierService = createResourceService<Supplier>("suppliers");
export const customerService = createResourceService<Customer>("customers");
export const productService = createResourceService<Product>("products");
export const purchaseService = createResourceService<Purchase>("purchases");
export const saleService = createResourceService<Sale>("sales");
export const orderService = createResourceService<Order>("orders");

export const stockAdjustmentApi = {
  adjust: async (productId: number, payload: { new_quantity: number; reason: string }): Promise<StockAdjustment> => {
    const { data } = await apiClient.post<StockAdjustment>(`/products/${productId}/adjust-stock/`, payload);
    return data;
  },
  history: async (productId: number): Promise<StockAdjustment[]> => {
    const { data } = await apiClient.get<StockAdjustment[]>(`/products/${productId}/stock-history/`);
    return data;
  },
  list: async (params: Record<string, string | number | undefined> = {}) => {
    const { data } = await apiClient.get<{ results: StockAdjustment[]; count: number }>("/stock-adjustments/", {
      params,
    });
    return data;
  },
};

export const orderApi = {
  ...orderService,
  updateStatus: async (id: number, status: Order["status"]): Promise<Order> => {
    const { data } = await apiClient.patch<Order>(`/orders/${id}/status/`, { status });
    return data;
  },
};

export const alertService = {
  list: async (params: Record<string, string | number | undefined> = {}) => {
    const { data } = await apiClient.get<{ results: StockAlert[]; count: number }>("/alerts/", { params });
    return data;
  },
  resolve: async (id: number): Promise<StockAlert> => {
    const { data } = await apiClient.post<StockAlert>(`/alerts/${id}/resolve/`);
    return data;
  },
};

export const dashboardService = {
  get: async (): Promise<DashboardData> => {
    const { data } = await apiClient.get<DashboardData>("/dashboard/");
    return data;
  },
};
