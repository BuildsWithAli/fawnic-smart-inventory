import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { AlertCountProvider, useAlertCount } from "../hooks/useAlertCount";

const TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/products": "Products",
  "/categories": "Categories",
  "/brands": "Brands",
  "/warehouses": "Warehouses",
  "/stock": "Stock Adjustments",
  "/suppliers": "Suppliers",
  "/customers": "Customers",
  "/purchases": "Purchases",
  "/sales": "Sales",
  "/kanban": "Orders / Kanban",
  "/alerts": "AI Alerts",
  "/settings": "Settings",
};

function AppLayoutShell() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { count: alertCount, refresh: refreshAlertCount } = useAlertCount();

  // Refresh the bell on every navigation, on top of the provider's poll — so
  // resolving an alert or landing on a page reflects immediately.
  useEffect(() => {
    refreshAlertCount();
  }, [location.pathname, refreshAlertCount]);

  const title = TITLES[location.pathname] ?? "FAWNIC";

  return (
    <div className="flex min-h-screen bg-bg">
      <Sidebar
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed((c) => !c)}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar title={title} onOpenMobileSidebar={() => setMobileOpen(true)} alertCount={alertCount} />
        <main className="flex-1 p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function AppLayout() {
  return (
    <AlertCountProvider>
      <AppLayoutShell />
    </AlertCountProvider>
  );
}
