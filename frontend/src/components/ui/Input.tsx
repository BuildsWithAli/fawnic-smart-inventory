import { forwardRef, type InputHTMLAttributes } from "react";
import clsx from "clsx";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className, id, ...props }, ref) => {
    const inputId = id ?? props.name;
    return (
      <label className="flex flex-col gap-1.5" htmlFor={inputId}>
        {label && <span className="text-sm font-medium text-ink-soft">{label}</span>}
        <input
          ref={ref}
          id={inputId}
          className={clsx(
            "w-full rounded-lg border bg-surface px-3 py-2 text-sm text-ink placeholder:text-muted transition-colors",
            "focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent",
            error ? "border-danger" : "border-border",
            className,
          )}
          {...props}
        />
        {error && <span className="text-xs text-danger">{error}</span>}
        {!error && hint && <span className="text-xs text-muted">{hint}</span>}
      </label>
    );
  },
);
Input.displayName = "Input";
