import { CrudPage } from "../components/crud/CrudPage";
import { customerService } from "../services";
import type { Customer } from "../types/models";
import type { CrudConfig } from "../types/crud";

const config: CrudConfig<Customer> = {
  title: "Customers",
  singularLabel: "Customer",
  endpoint: customerService,
  searchPlaceholder: "Search customers...",
  emptyTitle: "No customers found",
  emptyDescription: "Add your first customer to start recording sales.",
  columns: [
    { key: "name", header: "Name", render: (row) => <span className="font-medium text-ink">{row.name}</span> },
    { key: "email", header: "Email", render: (row) => row.email || "—" },
    { key: "phone", header: "Phone", render: (row) => row.phone || "—" },
  ],
  fields: [
    { name: "name", label: "Name", type: "text", required: true },
    { name: "email", label: "Email", type: "text" },
    { name: "phone", label: "Phone", type: "text" },
    { name: "address", label: "Address", type: "textarea" },
  ],
};

export function CustomersPage() {
  return <CrudPage config={config} />;
}
