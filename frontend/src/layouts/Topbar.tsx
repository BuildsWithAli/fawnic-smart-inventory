import { Menu, Search, BellRing } from "lucide-react";
import { Link } from "react-router-dom";

interface TopbarProps {
  title: string;
  onOpenMobileSidebar: () => void;
  alertCount?: number;
}

export function Topbar({ title, onOpenMobileSidebar, alertCount = 0 }: TopbarProps) {
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
      </div>
    </header>
  );
}
