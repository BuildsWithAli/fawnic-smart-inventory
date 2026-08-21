import { CrudPage } from "../components/crud/CrudPage";
import { supplierService } from "../services";
import type { Supplier } from "../types/models";
import type { CrudConfig } from "../types/crud";

const config: CrudConfig<Supplier> = {
  title: "Suppliers",
  singularLabel: "Supplier",
  endpoint: supplierService,
  searchPlaceholder: "Search suppliers...",
  emptyTitle: "No suppliers found",
  emptyDescription: "Add your first supplier to start recording purchases.",
  columns: [
    { key: "name", header: "Name", render: (row) => <span className="font-medium text-ink">{row.name}</span> },
    { key: "contact_name", header: "Contact", render: (row) => row.contact_name || "—" },
    { key: "email", header: "Email", render: (row) => row.email || "—" },
    { key: "phone", header: "Phone", render: (row) => row.phone || "—" },
  ],
  fields: [
    { name: "name", label: "Name", type: "text", required: true },
    { name: "contact_name", label: "Contact Name", type: "text" },
    { name: "email", label: "Email", type: "text" },
    { name: "phone", label: "Phone", type: "text" },
    { name: "address", label: "Address", type: "textarea" },
  ],
};

export function SuppliersPage() {
  return <CrudPage config={config} />;
}
