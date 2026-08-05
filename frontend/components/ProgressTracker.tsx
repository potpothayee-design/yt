"use client";

/** Live pipeline progress tracker (matches the production workflow). */

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { Job, StepState } from "@/lib/types";
import { cx } from "@/lib/utils";
import { Spinner } from "@/components/ui";

function StepIcon({ status }: { status: StepState["status"] }) {
  if (status === "done")
    return (
      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-emerald-500 text-xs font-bold text-white">
        ✔
      </span>
    );
  if (status === "failed")
    return (
      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-rose-500 text-xs font-bold text-white">
        ✖
      </span>
    );
  if (status === "running")
    return (
      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-500 text-white">
        <Spinner className="h-3.5 w-3.5" />
      </span>
    );
  return (
    <span className="flex h-7 w-7 items-center justify-center rounded-full border-2 border-slate-300 text-[10px] font-bold text-slate-400 dark:border-slate-600" />
  );
}

export function ProgressTracker({
  jobId,
  projectStatus,
  pollMs = 2000,
  compact = false,
}: {
  jobId?: number | null;
  projectStatus?: string | null;
  pollMs?: number;
  compact?: boolean;
}) {
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    const poll = async () => {
      try {
        const data = await api.get<Job>(`/api/v1/jobs/${jobId}`);
        if (cancelled) return;
        setJob(data);
        const running = data.status === "queued" || data.status === "running";
        if (running) timer = setTimeout(poll, pollMs);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "poll failed");
      }
    };
    poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [jobId, pollMs]);

  const steps = useMemo(() => job?.steps ?? [], [job]);

  if (!jobId) return null;

  const doneCount = steps.filter((s) => s.status === "done").length;
  const total = Math.max(1, steps.length - 1); // exclude terminal upload approval gate

  return (
    <div className="card p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">
          Generation Pipeline
        </h3>
        <span className="text-xs font-semibold text-slate-400">
          {doneCount}/{total} steps
        </span>
      </div>
      {error && <p className="mb-2 text-xs text-rose-500">{error}</p>}
      <div className="mb-4 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
        <div
          className="h-full rounded-full bg-brand-500 transition-all duration-700"
          style={{ width: `${Math.min(100, (doneCount / total) * 100)}%` }}
        />
      </div>
      <ol className={cx("space-y-2.5", compact && "grid grid-cols-2 gap-2 space-y-0 md:grid-cols-3")}>
        {steps.map((step) => {
          const isUploadGate = step.name === "upload";
          const label =
            isUploadGate && step.status === "pending"
              ? projectStatus === "published"
                ? "Uploaded ✔"
                : "Pending Approval"
              : step.label;
          return (
            <li key={step.name} className="flex items-center gap-3">
              <StepIcon status={step.status} />
              <div className="min-w-0 flex-1">
                <p
                  className={cx(
                    "truncate text-sm font-medium",
                    step.status === "running" && "text-brand-600 dark:text-brand-300",
                    step.status === "pending" && "text-slate-400 dark:text-slate-500"
                  )}
                >
                  {label}
                </p>
                {step.status === "running" && (
                  <p className="text-xs text-slate-400">Generating…</p>
                )}
              </div>
              {step.status === "done" && (
                <span className="text-xs font-semibold text-emerald-500">✔</span>
              )}
            </li>
          );
        })}
      </ol>
      {job && (job.status === "failed" || job.error) && (
        <p className="mt-3 rounded-lg bg-rose-500/10 p-2 text-xs text-rose-600 dark:text-rose-400">
          {job.error ?? "generation failed — you can retry; completed steps resume automatically"}
        </p>
      )}
    </div>
  );
}
