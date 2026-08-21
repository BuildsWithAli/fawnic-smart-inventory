import type { ReactNode } from "react";
import clsx from "clsx";
import type { ColumnDef } from "../../types/crud";
import { TableSkeleton } from "../ui/Skeleton";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";

interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  rows: T[];
  rowKey: (row: T) => number | string;
  isLoading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  emptyTitle?: string;
  emptyDescription?: string;
  rowActions?: (row: T) => ReactNode;
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  isLoading,
  error,
  onRetry,
  emptyTitle = "No results found",
  emptyDescription = "Try adjusting your filters or search terms.",
  rowActions,
}: DataTableProps<T>) {
  if (isLoading) return <TableSkeleton cols={columns.length} />;
  if (error) return <ErrorState message={error} onRetry={onRetry} />;
  if (rows.length === 0) return <EmptyState title={emptyTitle} description={emptyDescription} />;

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs font-medium uppercase tracking-wide text-muted">
            {columns.map((col) => (
              <th key={col.key} className={clsx("px-5 py-3 font-medium", col.className)}>
                {col.header}
              </th>
            ))}
            {rowActions && <th className="px-5 py-3" />}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {rows.map((row) => (
            <tr key={rowKey(row)} className="transition-colors hover:bg-surface-hover">
              {columns.map((col) => (
                <td key={col.key} className={clsx("px-5 py-3.5 text-ink-soft", col.className)}>
                  {col.render(row)}
                </td>
              ))}
              {rowActions && <td className="px-5 py-3.5 text-right">{rowActions(row)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
