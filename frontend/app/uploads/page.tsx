"use client";

/** Uploads: history, statuses, retry and refresh. */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Project, UploadRecord } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { EmptyState, Spinner, StatusBadge } from "@/components/ui";

export default function UploadsPage() {
  const [uploads, setUploads] = useState<UploadRecord[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<number | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [u, p] = await Promise.all([
        api.get<UploadRecord[]>("/api/v1/uploads"),
        api.get<Project[]>("/api/v1/projects"),
      ]);
      setUploads(u);
      setProjects(p);
    } catch {
      /* transient */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 8000);
    return () => clearInterval(timer);
  }, [refresh]);

  const act = async (upload: UploadRecord, action: "retry" | "refresh") => {
    setBusy(upload.id);
    try {
      await api.post(`/api/v1/uploads/${upload.id}/${action}`);
      await refresh();
    } catch {
      /* surfaced via refresh */
    } finally {
      setBusy(null);
    }
  };

  const projectName = (id: number) => {
    const p = projects.find((x) => x.id === id);
    return p ? p.title || p.topic : `Project #${id}`;
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold">Uploads</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Every YouTube upload — requested explicitly by you, tracked end to end.
        </p>
      </div>

      {loading ? (
        <p className="py-10 text-center text-sm text-slate-400">Loading uploads…</p>
      ) : uploads.length === 0 ? (
        <EmptyState
          icon="🚀"
          title="No uploads yet"
          message="Approve a finished video from its preview page and it will be uploaded to your connected YouTube channel."
          action={<Link href="/projects" className="btn-primary">Browse Projects</Link>}
        />
      ) : (
        <div className="space-y-3">
          {uploads.map((upload) => (
            <div key={upload.id} className="card p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="min-w-0">
                  <Link
                    href={`/projects/${upload.project_id}`}
                    className="truncate text-sm font-bold hover:text-brand-500"
                  >
                    {projectName(upload.project_id)}
                  </Link>
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-400">
                    <span>{formatDate(upload.created_at)}</span>
                    <span>•</span>
                    <span className="capitalize">{upload.privacy}</span>
                    <span>•</span>
                    <span>{upload.made_for_kids ? "made for kids" : "not for kids"}</span>
                    {upload.scheduled_at && (
                      <>
                        <span>•</span>
                        <span>⏰ {formatDate(upload.scheduled_at)}</span>
                      </>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={upload.status} kind="upload" />
                  {upload.youtube_video_id && (
                    <a
                      className="btn-secondary px-3 py-1.5 text-xs"
                      href={`https://www.youtube.com/watch?v=${upload.youtube_video_id}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Watch ↗
                    </a>
                  )}
                  <button
                    className="btn-secondary px-3 py-1.5 text-xs"
                    disabled={busy === upload.id}
                    onClick={() => act(upload, "refresh")}
                  >
                    {busy === upload.id ? <Spinner /> : "Refresh"}
                  </button>
                  {upload.status === "failed" && (
                    <button
                      className="btn-primary px-3 py-1.5 text-xs"
                      disabled={busy === upload.id}
                      onClick={() => act(upload, "retry")}
                    >
                      {busy === upload.id ? <Spinner /> : "Retry"}
                    </button>
                  )}
                  <button
                    className="btn-secondary px-2 py-1.5 text-xs"
                    onClick={() => setExpanded(expanded === upload.id ? null : upload.id)}
                  >
                    {expanded === upload.id ? "▲" : "▼"}
                  </button>
                </div>
              </div>
              {upload.last_error && (
                <p className="mt-2 rounded-lg bg-rose-500/10 p-2 text-xs text-rose-600 dark:text-rose-400">
                  {upload.last_error}
                </p>
              )}
              {expanded === upload.id && upload.history && (
                <ol className="mt-3 space-y-1.5 border-t border-slate-100 pt-3 text-xs dark:border-slate-800">
                  {upload.history.map((h, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="shrink-0 font-mono text-slate-400">
                        {formatDate(h.time)}
                      </span>
                      <span className="font-semibold">{h.status}:</span>
                      <span className="text-slate-500 dark:text-slate-400">{h.message}</span>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
