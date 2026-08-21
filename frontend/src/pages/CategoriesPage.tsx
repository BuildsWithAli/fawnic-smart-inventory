import { CrudPage } from "../components/crud/CrudPage";
import { categoryService } from "../services";
import type { Category } from "../types/models";
import type { CrudConfig } from "../types/crud";
import { formatDate } from "../utils/format";

const config: CrudConfig<Category> = {
  title: "Categories",
  singularLabel: "Category",
  endpoint: categoryService,
  searchPlaceholder: "Search categories...",
  emptyTitle: "No categories found",
  emptyDescription: "Add your first category to start grouping products.",
  columns: [
    { key: "name", header: "Name", render: (row) => <span className="font-medium text-ink">{row.name}</span> },
    { key: "description", header: "Description", render: (row) => row.description || "—" },
    { key: "created_at", header: "Created", render: (row) => formatDate(row.created_at) },
  ],
  fields: [
    { name: "name", label: "Name", type: "text", required: true },
    { name: "description", label: "Description", type: "textarea" },
  ],
};

export function CategoriesPage() {
  return <CrudPage config={config} />;
}
