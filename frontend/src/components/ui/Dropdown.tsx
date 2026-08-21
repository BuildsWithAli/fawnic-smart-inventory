import { useEffect, useRef, useState, type ReactNode } from "react";
import clsx from "clsx";

interface DropdownProps {
  trigger: ReactNode;
  children: ReactNode;
  align?: "left" | "right";
}

export function Dropdown({ trigger, children, align = "right" }: DropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const onClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setIsOpen(false);
    };
    const onEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsOpen(false);
    };
    document.addEventListener("mousedown", onClickOutside);
    document.addEventListener("keydown", onEscape);
    return () => {
      document.removeEventListener("mousedown", onClickOutside);
      document.removeEventListener("keydown", onEscape);
    };
  }, [isOpen]);

  return (
    <div className="relative" ref={ref}>
      <button type="button" onClick={() => setIsOpen((v) => !v)} className="flex items-center">
        {trigger}
      </button>
      {isOpen && (
        <div
          className={clsx(
            "absolute top-full z-30 mt-2 min-w-[180px] rounded-lg border border-border bg-surface py-1 shadow-lg",
            align === "right" ? "right-0" : "left-0",
          )}
          onClick={() => setIsOpen(false)}
        >
          {children}
        </div>
      )}
    </div>
  );
}

export function DropdownItem({
  children,
  onClick,
  danger,
}: {
  children: ReactNode;
  onClick?: () => void;
  danger?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        "flex w-full items-center gap-2 px-3.5 py-2 text-left text-sm hover:bg-surface-hover",
        danger ? "text-danger" : "text-ink-soft",
      )}
    >
      {children}
    </button>
  );
}
