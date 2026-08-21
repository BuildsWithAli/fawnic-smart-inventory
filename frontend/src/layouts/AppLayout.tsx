import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { alertService } from "../services";

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

export function AppLayout() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    const fetchCount = async () => {
      try {
        const data = await alertService.list({ resolved: "false" });
        setAlertCount(data.count);
      } catch {
        /* non-critical widget */
      }
    };
    void fetchCount();
    const interval = setInterval(fetchCount, 60_000);
    return () => clearInterval(interval);
  }, [location.pathname]);

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
