import type { ReactNode } from "react";

export interface ColumnDef<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
}

export type FieldType = "text" | "number" | "textarea" | "select";

export interface FieldOption {
  value: string | number;
  label: string;
}

export interface FieldDef<T> {
  name: keyof T & string;
  label: string;
  type: FieldType;
  required?: boolean;
  options?: FieldOption[];
  placeholder?: string;
  step?: string;
  min?: number;
}

export interface CrudConfig<T extends { id: number }> {
  title: string;
  singularLabel: string;
  endpoint: {
    list: (params: Record<string, string | number | undefined>) => Promise<{ results: T[]; count: number }>;
    create: (payload: Partial<T>) => Promise<T>;
    update: (id: number, payload: Partial<T>) => Promise<T>;
    remove: (id: number) => Promise<void>;
  };
  columns: ColumnDef<T>[];
  fields: FieldDef<T>[];
  searchPlaceholder?: string;
  emptyTitle?: string;
  emptyDescription?: string;
  getInitialValues?: (row?: T) => Record<string, unknown>;
}
