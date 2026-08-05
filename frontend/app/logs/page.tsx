"use client";

/** Logs: full event stream with filters. */

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { LogEntry, Project } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const LEVELS = ["", "INFO", "WARNING", "ERROR"];

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [level, setLevel] = useState("");
  const [projectId, setProjectId] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<Project[]>("/api/v1/projects").then(setProjects).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const qs = new URLSearchParams({ limit: "400" });
    if (level) qs.set("level", level);
    if (projectId) qs.set("project_id", projectId);
    api
      .get<LogEntry[]>(`/api/v1/logs?${qs.toString()}`)
      .then(setLogs)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [level, projectId]);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold">Logs</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Full audit trail of everything the studio does.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        {LEVELS.map((l) => (
          <button
            key={l || "all"}
            onClick={() => setLevel(l)}
            className={level === l ? "btn-primary px-3.5 py-1.5 text-xs" : "btn-secondary px-3.5 py-1.5 text-xs"}
          >
            {l || "All levels"}
          </button>
        ))}
        <select className="input max-w-64 ml-auto" value={projectId} onChange={(e) => setProjectId(e.target.value)}>
          <option value="">All projects</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.title || p.topic}
            </option>
          ))}
        </select>
      </div>

      <div className="card p-0">
        {loading ? (
          <p className="py-10 text-center text-sm text-slate-400">Loading logs…</p>
        ) : logs.length === 0 ? (
          <p className="py-10 text-center text-sm text-slate-400">No log entries yet.</p>
        ) : (
          <ul className="nice-scroll max-h-[70vh] divide-y divide-slate-100 overflow-y-auto font-mono text-xs dark:divide-slate-800">
            {logs.map((log) => (
              <li key={log.id} className="flex items-start gap-3 px-4 py-2.5">
                <span
                  className={
                    "mt-0.5 inline-block w-16 shrink-0 rounded px-1.5 py-0.5 text-center text-[10px] font-bold " +
                    (log.level === "ERROR"
                      ? "bg-rose-500/15 text-rose-500"
                      : log.level === "WARNING"
                        ? "bg-amber-500/15 text-amber-500"
                        : "bg-brand-500/10 text-brand-500")
                  }
                >
                  {log.level}
                </span>
                <span className="w-32 shrink-0 text-slate-400">{formatDate(log.created_at)}</span>
                <span className="min-w-0 flex-1 break-words">
                  {log.project_id && (
                    <Link href={`/projects/${log.project_id}`} className="mr-2 text-brand-500 hover:underline">
                      #{log.project_id}
                    </Link>
                  )}
                  {log.message}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
