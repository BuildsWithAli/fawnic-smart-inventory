import { CrudPage } from "../components/crud/CrudPage";
import { brandService } from "../services";
import type { Brand } from "../types/models";
import type { CrudConfig } from "../types/crud";
import { formatDate } from "../utils/format";

const config: CrudConfig<Brand> = {
  title: "Brands",
  singularLabel: "Brand",
  endpoint: brandService,
  searchPlaceholder: "Search brands...",
  emptyTitle: "No brands found",
  emptyDescription: "Add your first brand to start organizing products by line.",
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

export function BrandsPage() {
  return <CrudPage config={config} />;
}
