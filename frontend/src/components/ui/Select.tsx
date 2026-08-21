import { forwardRef, type SelectHTMLAttributes } from "react";
import clsx from "clsx";
import { ChevronDown } from "lucide-react";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, className, id, children, ...props }, ref) => {
    const selectId = id ?? props.name;
    return (
      <label className="flex flex-col gap-1.5" htmlFor={selectId}>
        {label && <span className="text-sm font-medium text-ink-soft">{label}</span>}
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            className={clsx(
              "w-full appearance-none rounded-lg border bg-surface px-3 py-2 pr-9 text-sm text-ink transition-colors",
              "focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent",
              error ? "border-danger" : "border-border",
              className,
            )}
            {...props}
          >
            {children}
          </select>
          <ChevronDown size={15} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-muted" />
        </div>
        {error && <span className="text-xs text-danger">{error}</span>}
      </label>
    );
  },
);
Select.displayName = "Select";
