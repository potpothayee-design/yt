"use client";

/** Dashboard: overview stats, recent projects, quick actions. */

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, media } from "@/lib/api";
import type { LogEntry, Project, UploadRecord } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Card, SectionTitle, StatCard, StatusBadge } from "@/components/ui";

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [uploads, setUploads] = useState<UploadRecord[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  useEffect(() => {
    api.get<Project[]>("/api/v1/projects").then(setProjects).catch(() => {});
    api.get<UploadRecord[]>("/api/v1/uploads").then(setUploads).catch(() => {});
    api.get<LogEntry[]>("/api/v1/logs?limit=8").then(setLogs).catch(() => {});
  }, []);

  const stats = {
    projects: projects.length,
    review: projects.filter((p) => p.status === "ready_for_review").length,
    generating: projects.filter((p) => p.status === "generating").length,
    published: projects.filter((p) => p.status === "published").length,
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold">Dashboard</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Everything at a glance — nothing publishes without your approval.
          </p>
        </div>
        <Link href="/generator" className="btn-primary">
          🎬 Generate a Video
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Projects" value={stats.projects} icon="🗂️" />
        <StatCard label="Ready for Review" value={stats.review} icon="👀" />
        <StatCard label="Generating" value={stats.generating} icon="⚙️" />
        <StatCard label="Published" value={stats.published} icon="🚀" />
      </div>

      <Card>
        <SectionTitle
          title="Recent Projects"
          subtitle="Latest productions in the studio"
          action={
            <Link href="/projects" className="text-sm font-semibold text-brand-500 hover:underline">
              View all →
            </Link>
          }
        />
        {projects.length === 0 ? (
          <p className="py-6 text-center text-sm text-slate-400">
            No projects yet — create your first kids video from the Generator.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.slice(0, 6).map((p) => (
              <Link
                key={p.id}
                href={`/projects/${p.id}`}
                className="group overflow-hidden rounded-2xl border border-slate-200 transition hover:shadow-md dark:border-slate-800"
              >
                <div className="aspect-video w-full bg-slate-100 dark:bg-slate-800">
                  {media(p.thumbnail_url) ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={media(p.thumbnail_url) ?? ""}
                      alt={p.topic}
                      className="h-full w-full object-cover transition group-hover:scale-[1.02]"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center text-3xl">🎬</div>
                  )}
                </div>
                <div className="p-3.5">
                  <p className="truncate text-sm font-bold">
                    {p.title || p.topic}
                  </p>
                  <div className="mt-1.5 flex items-center justify-between">
                    <StatusBadge status={p.status} />
                    <span className="text-xs text-slate-400">{formatDate(p.updated_at)}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <SectionTitle title="Recent Uploads" />
          {uploads.length === 0 ? (
            <p className="py-4 text-center text-sm text-slate-400">
              No uploads yet. Approve a finished video to publish it.
            </p>
          ) : (
            <ul className="divide-y divide-slate-100 dark:divide-slate-800">
              {uploads.slice(0, 6).map((u) => (
                <li key={u.id} className="flex items-center justify-between py-2.5 text-sm">
                  <span className="truncate">Project #{u.project_id}</span>
                  <StatusBadge status={u.status} kind="upload" />
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card>
          <SectionTitle title="Latest Activity" />
          {logs.length === 0 ? (
            <p className="py-4 text-center text-sm text-slate-400">No activity yet.</p>
          ) : (
            <ul className="nice-scroll max-h-72 space-y-2 overflow-y-auto pr-1">
              {logs.map((log) => (
                <li key={log.id} className="flex items-start gap-2.5 text-sm">
                  <span
                    className={
                      log.level === "ERROR"
                        ? "text-rose-500"
                        : log.level === "WARNING"
                          ? "text-amber-500"
                          : "text-brand-500"
                    }
                  >
                    ●
                  </span>
                  <div className="min-w-0">
                    <p className="truncate">{log.message}</p>
                    <p className="text-xs text-slate-400">{formatDate(log.created_at)}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
