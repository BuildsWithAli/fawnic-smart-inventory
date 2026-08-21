import { CrudPage } from "../components/crud/CrudPage";
import { warehouseService } from "../services";
import type { Warehouse } from "../types/models";
import type { CrudConfig } from "../types/crud";

const config: CrudConfig<Warehouse> = {
  title: "Warehouses",
  singularLabel: "Warehouse",
  endpoint: warehouseService,
  searchPlaceholder: "Search warehouses...",
  emptyTitle: "No warehouses found",
  emptyDescription: "Add your first warehouse to start assigning stock locations.",
  columns: [
    { key: "name", header: "Name", render: (row) => <span className="font-medium text-ink">{row.name}</span> },
    { key: "location", header: "Location", render: (row) => row.location || "—" },
    { key: "capacity_notes", header: "Capacity Notes", render: (row) => row.capacity_notes || "—" },
  ],
  fields: [
    { name: "name", label: "Name", type: "text", required: true },
    { name: "location", label: "Location", type: "text" },
    { name: "capacity_notes", label: "Capacity Notes", type: "textarea" },
  ],
};

export function WarehousesPage() {
  return <CrudPage config={config} />;
}
