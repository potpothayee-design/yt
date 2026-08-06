"use client";

/** Projects: all productions with status filters. */

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, media } from "@/lib/api";
import type { Project } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { EmptyState, StatusBadge } from "@/components/ui";

const FILTERS = [
  { value: "", label: "All" },
  { value: "draft", label: "Drafts" },
  { value: "generating", label: "Generating" },
  { value: "ready_for_review", label: "Ready for Review" },
  { value: "failed", label: "Failed" },
  { value: "published", label: "Published" },
];

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    setLoading(true);
    const qs = filter ? `?status=${filter}` : "";
    api
      .get<Project[]>(`/api/v1/projects${qs}`)
      .then(setProjects)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [filter]);

  const handleDelete = async (p: Project) => {
    const name = p.title || p.topic;
    if (!window.confirm(`Delete "${name}" for good?\n\nThis removes the video, images, audio and all project data. This cannot be undone.`)) return;
    setDeletingId(p.id);
    try {
      await api.delete(`/api/v1/projects/${p.id}`);
      setProjects((prev) => prev.filter((x) => x.id !== p.id));
    } catch {
      window.alert("Could not delete the project — please try again.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold">Projects</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Every production from topic to published draft.
          </p>
        </div>
        <Link href="/generator" className="btn-primary">
          ＋ New Video
        </Link>
      </div>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={
              filter === f.value
                ? "btn-primary px-3.5 py-1.5 text-xs"
                : "btn-secondary px-3.5 py-1.5 text-xs"
            }
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="py-10 text-center text-sm text-slate-400">Loading projects…</p>
      ) : projects.length === 0 ? (
        <EmptyState
          icon="🗂️"
          title="No projects here yet"
          message="Generate your first kids video — the whole pipeline runs automatically and waits for your review."
          action={
            <Link href="/generator" className="btn-primary">
              Generate a Video
            </Link>
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} onDelete={handleDelete}
                         deleting={deletingId === p.id} />
          ))}
        </div>
      )}
    </div>
  );
}

function ProjectCard({ project: p, onDelete, deleting }: {
  project: Project;
  onDelete: (p: Project) => void;
  deleting: boolean;
}) {
  return (
    <div className="group card relative overflow-hidden p-0 transition hover:-translate-y-0.5 hover:shadow-lg">
      <button
        type="button"
        title="Delete project"
        aria-label={`Delete ${p.title || p.topic}`}
        disabled={deleting}
        onClick={(e) => {
          e.stopPropagation();
          onDelete(p);
        }}
        className="absolute right-2 top-2 z-10 rounded-lg bg-white/85 px-2 py-1 text-sm opacity-0 shadow transition group-hover:opacity-100 hover:bg-rose-50 hover:text-rose-600 disabled:opacity-50 dark:bg-slate-900/85 dark:hover:bg-rose-950"
      >
        {deleting ? "…" : "🗑️"}
      </button>
      <Link href={`/projects/${p.id}`} className="block">
        <div className="aspect-video w-full bg-slate-100 dark:bg-slate-800">
          {media(p.thumbnail_url) ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={media(p.thumbnail_url) ?? ""}
              alt={p.topic}
              className="h-full w-full object-cover transition group-hover:scale-[1.02]"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-4xl">
              {p.status === "generating" ? "⚙️" : "🎬"}
            </div>
          )}
        </div>
        <div className="p-4">
          <p className="truncate font-bold">{p.title || p.topic}</p>
          <p className="truncate text-xs text-slate-500 dark:text-slate-400">
            Topic: {p.topic}
          </p>
          {p.error && (
            <p className="mt-1 truncate text-xs text-rose-500">{p.error}</p>
          )}
          <div className="mt-2 flex items-center justify-between">
            <StatusBadge status={p.status} />
            <span className="text-xs text-slate-400">{formatDate(p.updated_at)}</span>
          </div>
        </div>
      </Link>
    </div>
  );
}
