import { forwardRef, type ButtonHTMLAttributes } from "react";
import clsx from "clsx";
import { Loader2 } from "lucide-react";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  isLoading?: boolean;
}

const VARIANT_STYLES: Record<Variant, string> = {
  primary: "bg-accent text-white hover:bg-accent-dark border border-transparent shadow-sm",
  secondary: "bg-surface text-ink border border-border hover:bg-surface-hover",
  ghost: "bg-transparent text-ink-soft hover:bg-surface-hover border border-transparent",
  danger: "bg-danger text-white hover:bg-danger/90 border border-transparent shadow-sm",
};

const SIZE_STYLES: Record<Size, string> = {
  sm: "text-xs px-2.5 py-1.5 gap-1.5",
  md: "text-sm px-3.5 py-2 gap-2",
  lg: "text-sm px-5 py-2.5 gap-2",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", isLoading, className, children, disabled, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled || isLoading}
      className={clsx(
        "inline-flex items-center justify-center rounded-lg font-medium transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 focus-visible:ring-offset-1",
        VARIANT_STYLES[variant],
        SIZE_STYLES[size],
        className,
      )}
      {...props}
    >
      {isLoading && <Loader2 size={15} className="animate-spin" />}
      {children}
    </button>
  ),
);
Button.displayName = "Button";
