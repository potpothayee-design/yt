/** Small shared helpers. */

export function cx(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return "—";
  const s = Math.round(seconds);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  draft: { label: "Draft", color: "bg-slate-500/15 text-slate-500 dark:text-slate-300" },
  generating: { label: "Generating", color: "bg-amber-500/15 text-amber-600 dark:text-amber-400" },
  ready_for_review: { label: "Ready for Review", color: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400" },
  failed: { label: "Failed", color: "bg-rose-500/15 text-rose-600 dark:text-rose-400" },
  uploading: { label: "Uploading", color: "bg-sky-500/15 text-sky-600 dark:text-sky-400" },
  published: { label: "Published", color: "bg-brand-500/15 text-brand-600 dark:text-brand-300" },
};

export const UPLOAD_STATUS_LABELS: Record<string, { label: string; color: string }> = {
  requested: { label: "Requested", color: "bg-slate-500/15 text-slate-500 dark:text-slate-300" },
  uploading: { label: "Uploading", color: "bg-sky-500/15 text-sky-600 dark:text-sky-300" },
  processing: { label: "Processing", color: "bg-amber-500/15 text-amber-600 dark:text-amber-400" },
  published: { label: "Published", color: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400" },
  draft_saved: { label: "Saved as Draft", color: "bg-brand-500/15 text-brand-600 dark:text-brand-300" },
  scheduled: { label: "Scheduled", color: "bg-violet-500/15 text-violet-600 dark:text-violet-300" },
  failed: { label: "Failed", color: "bg-rose-500/15 text-rose-600 dark:text-rose-400" },
};
