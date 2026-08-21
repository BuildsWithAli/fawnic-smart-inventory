import type { ReactNode } from "react";
import clsx from "clsx";

type Tone = "neutral" | "success" | "warning" | "danger" | "accent";

const TONE_STYLES: Record<Tone, string> = {
  neutral: "bg-surface-hover text-ink-soft border-border",
  success: "bg-success-soft text-success border-success/20",
  warning: "bg-warning-soft text-warning border-warning/20",
  danger: "bg-danger-soft text-danger border-danger/20",
  accent: "bg-accent-soft text-accent-dark border-accent/20",
};

export function Badge({ tone = "neutral", children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        TONE_STYLES[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
