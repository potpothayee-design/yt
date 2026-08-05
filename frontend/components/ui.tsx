"use client";

/** Shared UI primitives. */

import { cx, STATUS_LABELS, UPLOAD_STATUS_LABELS } from "@/lib/utils";

export function Card({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return <div className={cx("card p-5", className)}>{children}</div>;
}

export function SectionTitle({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 className="text-lg font-bold">{title}</h2>
        {subtitle && (
          <p className="text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>
        )}
      </div>
      {action}
    </div>
  );
}

export function StatusBadge({ status, kind }: { status: string; kind?: "upload" }) {
  const map = kind === "upload" ? UPLOAD_STATUS_LABELS : STATUS_LABELS;
  const entry = map[status] ?? { label: status, color: "bg-slate-500/15 text-slate-500" };
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold",
        entry.color
      )}
    >
      {entry.label}
    </span>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      className={cx(
        "inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent",
        className
      )}
    />
  );
}

export function EmptyState({
  icon,
  title,
  message,
  action,
}: {
  icon: string;
  title: string;
  message: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="card flex flex-col items-center gap-3 px-6 py-14 text-center">
      <span className="text-4xl">{icon}</span>
      <h3 className="text-base font-bold">{title}</h3>
      <p className="max-w-md text-sm text-slate-500 dark:text-slate-400">{message}</p>
      {action}
    </div>
  );
}

export function StatCard({
  label,
  value,
  icon,
  hint,
}: {
  label: string;
  value: string | number;
  icon: string;
  hint?: string;
}) {
  return (
    <div className="card flex items-center gap-4 p-5">
      <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-500/10 text-2xl">
        {icon}
      </span>
      <div className="min-w-0">
        <p className="truncate text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
          {label}
        </p>
        <p className="text-2xl font-extrabold">{value}</p>
        {hint && <p className="text-xs text-slate-400">{hint}</p>}
      </div>
    </div>
  );
}
