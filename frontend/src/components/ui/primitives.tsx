import type { ReactNode } from "react";
import * as Tooltip from "@radix-ui/react-tooltip";
import { Spinner } from "./spinner";

/** Page title block used at the top of every routed page. */
export function PageHeader({ title, sub }: { title: string; sub?: string }) {
  return (
    <header className="mb-6">
      <h1 className="text-2xl font-semibold tracking-tight text-forest-900">{title}</h1>
      {sub ? <p className="mt-1 text-sm text-forest-900/60">{sub}</p> : null}
    </header>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <section className={`border border-paper-300 bg-white ${className}`}>{children}</section>
  );
}

export function Button({
  children,
  onClick,
  variant = "primary",
  disabled,
  type = "button",
  className = "",
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  disabled?: boolean;
  type?: "button" | "submit";
  className?: string;
}) {
  const styles = {
    primary: "bg-forest-600 text-paper-50 hover:bg-forest-700 disabled:bg-forest-900/20",
    secondary: "border border-forest-600 text-forest-700 hover:bg-forest-50",
    ghost: "text-forest-900/70 hover:bg-paper-200",
    danger: "bg-clay-600 text-paper-50 hover:bg-clay-500",
  }[variant];
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${styles} ${className}`}
    >
      {children}
    </button>
  );
}

export function ErrorNote({ children }: { children: ReactNode }) {
  return (
    <div role="alert" className="border border-clay-500 bg-clay-500/10 px-4 py-3 text-sm text-clay-600">
      {children}
    </div>
  );
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-forest-900/50">
      <Spinner className="text-forest-700/70" />
      <span>{label}</span>
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="border border-dashed border-paper-300 px-4 py-8 text-sm text-forest-900/50">{children}</div>;
}

/** Icon-only metrics must carry tooltips (handoff §6.1). */
export function IconTip({ label, children }: { label: string; children: ReactNode }) {
  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>{children}</Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content side="top" sideOffset={4} className="bg-forest-900 px-2 py-1 text-xs text-paper-50">
          {label}
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}
