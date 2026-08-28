import { useEffect, useMemo, useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { DataTable } from "../components/crud/DataTable";
import { FilterBar } from "../components/crud/FilterBar";
import { SeverityBadge } from "../components/crud/StatusBadge";
import { Badge } from "../components/ui/Badge";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../hooks/useToast";
import { useAlertCount } from "../hooks/useAlertCount";
import { extractErrorMessage } from "../api/client";
import { alertService } from "../services";
import type { StockAlert } from "../types/models";
import { formatDate } from "../utils/format";

export function AlertsPage() {
  const { show } = useToast();
  const { canWrite } = useAuth();
  const { refresh: refreshAlertCount } = useAlertCount();
  const [rows, setRows] = useState<StockAlert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterValues, setFilterValues] = useState<Record<string, string>>({ resolved: "false" });
  const [resolvingId, setResolvingId] = useState<number | null>(null);

  const filters = useMemo(
    () => [
      {
        key: "resolved",
        label: "Status",
        options: [
          { value: "false", label: "Active" },
          { value: "true", label: "Resolved" },
        ],
      },
      {
        key: "severity",
        label: "Severity",
        options: [
          { value: "low", label: "Low" },
          { value: "medium", label: "Medium" },
          { value: "high", label: "High" },
          { value: "critical", label: "Critical" },
        ],
      },
    ],
    [],
  );

  const load = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await alertService.list(filterValues);
      setRows(data.results);
    } catch (err) {
      setError(extractErrorMessage(err, "Couldn't load AI stock alerts."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(filterValues)]);

  const handleResolve = async (alert: StockAlert) => {
    setResolvingId(alert.id);
    try {
      await alertService.resolve(alert.id);
      show("Alert marked as resolved.", "success");
      void load();
      refreshAlertCount();
    } catch (err) {
      show(extractErrorMessage(err, "Couldn't resolve this alert."), "error");
    } finally {
      setResolvingId(null);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <FilterBar
        filters={filters}
        values={filterValues}
        onChange={(key, value) => setFilterValues((prev) => ({ ...prev, [key]: value }))}
      />

      <Card className="overflow-hidden">
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
            {
              key: "order",
              header: "Order",
              render: (row) => (row.order ? <Badge tone="neutral">#{row.order}</Badge> : "—"),
            },
            { key: "severity", header: "Severity", render: (row) => <SeverityBadge severity={row.severity} /> },
            {
              key: "stock",
              header: "Current / Threshold",
              render: (row) => `${row.current_stock_at_alert} / ${row.reorder_threshold_at_alert}`,
            },
            {
              key: "suggested_quantity",
              header: "Suggested Reorder",
              render: (row) => (row.suggested_quantity != null ? row.suggested_quantity : "—"),
            },
            { key: "created_at", header: "Raised", render: (row) => formatDate(row.created_at) },
            {
              key: "resolved",
              header: "Status",
              render: (row) =>
                row.resolved ? <Badge tone="success">Resolved</Badge> : <Badge tone="danger">Active</Badge>,
            },
          ]}
          rows={rows}
          rowKey={(row) => row.id}
          isLoading={isLoading}
          error={error}
          onRetry={load}
          emptyTitle="No stock alerts"
          emptyDescription="The AI stock assistant raises alerts here when an order's products run low as it moves through production."
          rowActions={(row) =>
            !row.resolved && canWrite ? (
              <Button size="sm" variant="secondary" isLoading={resolvingId === row.id} onClick={() => handleResolve(row)}>
                <CheckCircle2 size={14} />
                Resolve
              </Button>
            ) : null
          }
        />
      </Card>
    </div>
  );
}
