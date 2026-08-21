import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Plus, Pencil, Trash2 } from "lucide-react";
import { Card } from "../ui/Card";
import { Button } from "../ui/Button";
import { DataTable } from "./DataTable";
import { SearchBar } from "./SearchBar";
import { FilterBar, type FilterConfig } from "./FilterBar";
import { FormModal } from "./FormModal";
import { ConfirmDialog } from "../ui/ConfirmDialog";
import { Pagination } from "../ui/Pagination";
import { useDebounce } from "../../hooks/useDebounce";
import { useToast } from "../../hooks/useToast";
import { extractErrorMessage } from "../../api/client";
import type { CrudConfig } from "../../types/crud";

const PAGE_SIZE = 20;

interface CrudPageProps<T extends { id: number }> {
  config: CrudConfig<T>;
  filters?: FilterConfig[];
  headerAction?: ReactNode;
}

export function CrudPage<T extends { id: number }>({ config, filters = [] }: CrudPageProps<T>) {
  const { show } = useToast();
  const [rows, setRows] = useState<T[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search);
  const [filterValues, setFilterValues] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editingRow, setEditingRow] = useState<T | null | "new">(null);
  const [isSaving, setIsSaving] = useState(false);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [deletingRow, setDeletingRow] = useState<T | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const params = useMemo(
    () => ({ search: debouncedSearch || undefined, page, ...filterValues }),
    [debouncedSearch, page, filterValues],
  );

  const load = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await config.endpoint.list(params);
      setRows(data.results);
      setCount(data.count);
    } catch (err) {
      setError(extractErrorMessage(err, "Couldn't load this list."));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(params)]);

  const openCreate = () => {
    setFormErrors({});
    setEditingRow("new");
  };

  const openEdit = (row: T) => {
    setFormErrors({});
    setEditingRow(row);
  };

  const handleSubmit = async (values: Record<string, unknown>) => {
    setIsSaving(true);
    setFormErrors({});
    try {
      if (editingRow === "new") {
        await config.endpoint.create(values as Partial<T>);
        show(`${config.singularLabel} created.`, "success");
      } else if (editingRow) {
        await config.endpoint.update(editingRow.id, values as Partial<T>);
        show(`${config.singularLabel} updated.`, "success");
      }
      setEditingRow(null);
      void load();
    } catch (err) {
      show(extractErrorMessage(err, `Couldn't save this ${config.singularLabel.toLowerCase()}.`), "error");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingRow) return;
    setIsDeleting(true);
    try {
      await config.endpoint.remove(deletingRow.id);
      show(`${config.singularLabel} deleted.`, "success");
      setDeletingRow(null);
      void load();
    } catch (err) {
      show(extractErrorMessage(err, `Couldn't delete this ${config.singularLabel.toLowerCase()}.`), "error");
    } finally {
      setIsDeleting(false);
    }
  };

  const initialValues =
    editingRow === "new"
      ? config.getInitialValues?.() ?? {}
      : editingRow
        ? config.getInitialValues?.(editingRow) ?? { ...editingRow }
        : {};

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
            placeholder={config.searchPlaceholder ?? `Search ${config.title.toLowerCase()}...`}
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
        <Button onClick={openCreate}>
          <Plus size={16} />
          Add {config.singularLabel}
        </Button>
      </div>

      <Card className="overflow-hidden">
        <DataTable
          columns={config.columns}
          rows={rows}
          rowKey={(row) => row.id}
          isLoading={isLoading}
          error={error}
          onRetry={load}
          emptyTitle={config.emptyTitle}
          emptyDescription={config.emptyDescription}
          rowActions={(row) => (
            <div className="flex items-center justify-end gap-1">
              <button
                onClick={() => openEdit(row)}
                className="rounded-md p-1.5 text-muted hover:bg-surface-hover hover:text-ink"
                aria-label={`Edit ${config.singularLabel}`}
              >
                <Pencil size={15} />
              </button>
              <button
                onClick={() => setDeletingRow(row)}
                className="rounded-md p-1.5 text-muted hover:bg-danger-soft hover:text-danger"
                aria-label={`Delete ${config.singularLabel}`}
              >
                <Trash2 size={15} />
              </button>
            </div>
          )}
        />
        {!isLoading && !error && rows.length > 0 && (
          <Pagination page={page} pageSize={PAGE_SIZE} total={count} onPageChange={setPage} />
        )}
      </Card>

      <FormModal
        isOpen={editingRow !== null}
        title={editingRow === "new" ? `Add ${config.singularLabel}` : `Edit ${config.singularLabel}`}
        fields={config.fields}
        initialValues={initialValues}
        isSaving={isSaving}
        errors={formErrors}
        onClose={() => setEditingRow(null)}
        onSubmit={handleSubmit}
      />

      <ConfirmDialog
        isOpen={deletingRow !== null}
        title={`Delete ${config.singularLabel}`}
        message={`Are you sure you want to delete this ${config.singularLabel.toLowerCase()}? This action cannot be undone.`}
        confirmLabel="Delete"
        danger
        isLoading={isDeleting}
        onConfirm={handleDelete}
        onCancel={() => setDeletingRow(null)}
      />
    </div>
  );
}
