import { Menu, Search, BellRing, Settings, LogOut } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { Dropdown, DropdownItem } from "../components/ui/Dropdown";
import { useAuth } from "../hooks/useAuth";

interface TopbarProps {
  title: string;
  onOpenMobileSidebar: () => void;
  alertCount?: number;
}

const ROLE_LABELS: Record<string, string> = {
  owner: "Owner",
  inventory_manager: "Inventory Manager",
  support: "Support",
};

export function Topbar({ title, onOpenMobileSidebar, alertCount = 0 }: TopbarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-4 border-b border-border bg-surface/90 px-4 backdrop-blur sm:px-6">
      <button
        onClick={onOpenMobileSidebar}
        className="rounded-md p-1.5 text-ink-soft hover:bg-surface-hover lg:hidden"
        aria-label="Open menu"
      >
        <Menu size={20} />
      </button>

      <h1 className="font-display text-lg font-medium text-ink">{title}</h1>

      <div className="ml-auto flex items-center gap-3">
        <div className="relative hidden sm:block">
          <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            placeholder="Search FAWNIC..."
            className="w-64 rounded-lg border border-border bg-surface py-2 pl-9 pr-3 text-sm text-ink placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
          />
        </div>
        <Link
          to="/alerts"
          className="relative rounded-lg p-2 text-ink-soft hover:bg-surface-hover"
          aria-label="View alerts"
        >
          <BellRing size={19} />
          {alertCount > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-danger px-1 text-[10px] font-semibold text-white">
              {alertCount > 9 ? "9+" : alertCount}
            </span>
          )}
        </Link>

        <Dropdown
          trigger={
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-soft font-display text-xs font-semibold text-accent-dark hover:ring-2 hover:ring-accent/30">
              {(user?.first_name?.[0] ?? user?.username?.[0] ?? "?").toUpperCase()}
            </span>
          }
        >
          <div className="border-b border-border px-3.5 py-2.5">
            <p className="truncate text-sm font-medium text-ink">{user?.first_name || user?.username}</p>
            <p className="truncate text-xs text-muted">{user ? ROLE_LABELS[user.role] : ""}</p>
          </div>
          <DropdownItem onClick={() => navigate("/settings")}>
            <Settings size={15} />
            Settings
          </DropdownItem>
          <DropdownItem onClick={logout} danger>
            <LogOut size={15} />
            Log out
          </DropdownItem>
        </Dropdown>
      </div>
    </header>
  );
}
