import { useEffect, useState } from "react";
import { Card, CardHeader } from "../components/ui/Card";
import { DataTable } from "../components/crud/DataTable";
import { Pagination } from "../components/ui/Pagination";
import { extractErrorMessage } from "../api/client";
import { stockAdjustmentApi } from "../services";
import type { StockAdjustment } from "../types/models";
import { formatDate } from "../utils/format";

const PAGE_SIZE = 20;

export function StockPage() {
  const [rows, setRows] = useState<StockAdjustment[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await stockAdjustmentApi.list({ page });
      setRows(data.results);
      setCount(data.count);
    } catch (err) {
      setError(extractErrorMessage(err, "Couldn't load the stock adjustment history."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  return (
    <Card className="overflow-hidden">
      <CardHeader title="Stock Adjustment History" subtitle="Full audit trail of manual stock corrections" />
      <DataTable
        columns={[
          {
            key: "product",
            header: "Product",
            render: (row) => (
              <div>
                <p className="font-medium text-ink">{row.product_name}</p>
                <p className="font-mono text-xs text-muted">{row.sku}</p>
              </div>
            ),
          },
          { key: "previous_quantity", header: "Previous", render: (row) => row.previous_quantity },
          { key: "new_quantity", header: "New", render: (row) => row.new_quantity },
          {
            key: "difference",
            header: "Change",
            render: (row) => (
              <span className={row.difference >= 0 ? "text-success" : "text-danger"}>
                {row.difference >= 0 ? `+${row.difference}` : row.difference}
              </span>
            ),
          },
          { key: "reason", header: "Reason", render: (row) => row.reason },
          { key: "user_name", header: "By", render: (row) => row.user_name ?? "System" },
          { key: "created_at", header: "Date", render: (row) => formatDate(row.created_at) },
        ]}
        rows={rows}
        rowKey={(row) => row.id}
        isLoading={isLoading}
        error={error}
        onRetry={load}
        emptyTitle="No stock adjustments yet"
        emptyDescription="Adjustments made from the Products page will appear here with a full audit trail."
      />
      {!isLoading && !error && rows.length > 0 && (
        <Pagination page={page} pageSize={PAGE_SIZE} total={count} onPageChange={setPage} />
      )}
    </Card>
  );
}
