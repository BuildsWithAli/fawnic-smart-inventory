import { NavLink } from "react-router-dom";
import clsx from "clsx";
import {
  LayoutDashboard,
  Package,
  Tags,
  Award,
  Warehouse,
  Boxes,
  Truck,
  Users,
  ShoppingCart,
  Receipt,
  Kanban,
  BellRing,
  Settings,
  LogOut,
  ChevronsLeft,
  X,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import fawnicLogo from "../assets/FAWNIC_logo.png";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/products", label: "Products", icon: Package },
  { to: "/categories", label: "Categories", icon: Tags },
  { to: "/brands", label: "Brands", icon: Award },
  { to: "/warehouses", label: "Warehouses", icon: Warehouse },
  { to: "/stock", label: "Stock", icon: Boxes },
  { to: "/suppliers", label: "Suppliers", icon: Truck },
  { to: "/customers", label: "Customers", icon: Users },
  { to: "/purchases", label: "Purchases", icon: ShoppingCart },
  { to: "/sales", label: "Sales", icon: Receipt },
  { to: "/kanban", label: "Orders / Kanban", icon: Kanban },
  { to: "/alerts", label: "AI Alerts", icon: BellRing },
  { to: "/settings", label: "Settings", icon: Settings, ownerOnly: true },
];

const ROLE_LABELS: Record<string, string> = {
  owner: "Owner",
  inventory_manager: "Inventory Manager",
  support: "Support",
};

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

export function Sidebar({ collapsed, onToggleCollapse, mobileOpen, onCloseMobile }: SidebarProps) {
  const { user, logout, isOwner } = useAuth();
  const navItems = NAV_ITEMS.filter((item) => !item.ownerOnly || isOwner);

  return (
    <>
      {mobileOpen && (
        <div className="fixed inset-0 z-30 bg-ink/40 lg:hidden" onClick={onCloseMobile} aria-hidden="true" />
      )}

      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-40 flex flex-col bg-sidebar text-white/90 transition-all duration-200 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0",
          collapsed ? "lg:w-[72px]" : "lg:w-60",
          "w-64",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
        )}
      >
        <div className="relative flex h-16 items-center gap-2.5 border-b border-sidebar-border px-5 before:absolute before:inset-x-4 before:bottom-0 before:h-px before:border-b before:border-dashed before:border-white/15">
          <img src={fawnicLogo} alt="FAWNIC" className="h-8 w-8 shrink-0 rounded-md object-cover" />
          {!collapsed && <span className="font-display text-lg font-medium tracking-tight text-white">FAWNIC</span>}
          <button
            onClick={onCloseMobile}
            className="ml-auto rounded-md p-1 text-white/60 hover:bg-sidebar-hover hover:text-white lg:hidden"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4">
          <ul className="flex flex-col gap-0.5">
            {navItems.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.end}
                  onClick={onCloseMobile}
                  className={({ isActive }) =>
                    clsx(
                      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-accent text-white"
                        : "text-white/65 hover:bg-sidebar-hover hover:text-white",
                      collapsed && "lg:justify-center",
                    )
                  }
                  title={collapsed ? item.label : undefined}
                >
                  <item.icon size={18} className="shrink-0" />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="border-t border-sidebar-border p-3">
          <button
            onClick={onToggleCollapse}
            className="mb-2 hidden w-full items-center justify-center gap-2 rounded-lg px-3 py-2 text-xs text-white/50 hover:bg-sidebar-hover hover:text-white lg:flex"
          >
            <ChevronsLeft size={15} className={clsx("transition-transform", collapsed && "rotate-180")} />
            {!collapsed && "Collapse"}
          </button>

          <div className={clsx("flex items-center gap-3 rounded-lg px-2 py-2", !collapsed && "bg-sidebar-hover")}>
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent-soft font-display text-xs font-semibold text-accent-dark">
              {(user?.first_name?.[0] ?? user?.username?.[0] ?? "?").toUpperCase()}
            </div>
            {!collapsed && (
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-white">{user?.first_name || user?.username}</p>
                <p className="truncate text-xs text-white/50">{user ? ROLE_LABELS[user.role] : ""}</p>
              </div>
            )}
            <button
              onClick={logout}
              className="shrink-0 rounded-md p-1.5 text-white/50 hover:bg-white/10 hover:text-white"
              aria-label="Log out"
              title="Log out"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
