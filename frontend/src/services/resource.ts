import { apiClient } from "../api/client";
import type { Paginated } from "../types/models";

export interface ListParams {
  search?: string;
  page?: number;
  ordering?: string;
  [key: string]: string | number | undefined;
}

/** Generic REST resource client — powers the CRUD engine for simple master-data endpoints. */
export function createResourceService<T, TWrite = Partial<T>>(endpoint: string) {
  return {
    list: async (params: ListParams = {}): Promise<Paginated<T>> => {
      const { data } = await apiClient.get<Paginated<T>>(`/${endpoint}/`, { params });
      return data;
    },
    get: async (id: number): Promise<T> => {
      const { data } = await apiClient.get<T>(`/${endpoint}/${id}/`);
      return data;
    },
    create: async (payload: TWrite): Promise<T> => {
      const { data } = await apiClient.post<T>(`/${endpoint}/`, payload);
      return data;
    },
    update: async (id: number, payload: TWrite): Promise<T> => {
      const { data } = await apiClient.patch<T>(`/${endpoint}/${id}/`, payload);
      return data;
    },
    remove: async (id: number): Promise<void> => {
      await apiClient.delete(`/${endpoint}/${id}/`);
    },
  };
}
