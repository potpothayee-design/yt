"use client";

/** Assets: browse every file the pipeline has produced. */

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, media } from "@/lib/api";
import type { Asset, Project } from "@/lib/types";
import { formatDate, formatDuration } from "@/lib/utils";
import { EmptyState } from "@/components/ui";

const KINDS = [
  { value: "", label: "All kinds" },
  { value: "image", label: "Scene images" },
  { value: "video_clip", label: "Video clips" },
  { value: "voice", label: "Voice" },
  { value: "music", label: "Music" },
  { value: "captions", label: "Captions" },
  { value: "thumbnail", label: "Thumbnails" },
  { value: "final_video", label: "Final videos" },
];

const KIND_ICONS: Record<string, string> = {
  image: "🖼️",
  video_clip: "🎞️",
  voice: "🎙️",
  music: "🎵",
  captions: "💬",
  thumbnail: "🌟",
  final_video: "🎬",
};

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [kind, setKind] = useState("");
  const [projectId, setProjectId] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<Project[]>("/api/v1/projects").then(setProjects).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const qs = new URLSearchParams();
    if (kind) qs.set("kind", kind);
    if (projectId) qs.set("project_id", projectId);
    api
      .get<Asset[]>(`/api/v1/assets?${qs.toString()}`)
      .then(setAssets)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [kind, projectId]);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold">Assets</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Every image, clip, voice track, music bed, caption file and thumbnail the
          pipeline produced.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <select className="input max-w-56" value={kind} onChange={(e) => setKind(e.target.value)}>
          {KINDS.map((k) => (
            <option key={k.value} value={k.value}>
              {k.label}
            </option>
          ))}
        </select>
        <select className="input max-w-64" value={projectId} onChange={(e) => setProjectId(e.target.value)}>
          <option value="">All projects</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.title || p.topic}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <p className="py-10 text-center text-sm text-slate-400">Loading assets…</p>
      ) : assets.length === 0 ? (
        <EmptyState
          icon="🧩"
          title="No assets found"
          message="Assets appear here as soon as the pipeline produces them."
          action={<Link href="/generator" className="btn-primary">Generate a Video</Link>}
        />
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {assets.map((asset) => (
            <AssetTile key={asset.id} asset={asset} />
          ))}
        </div>
      )}
    </div>
  );
}

function AssetTile({ asset }: { asset: Asset }) {
  const url = media(asset.url);
  const isImage = asset.kind === "image" || asset.kind === "thumbnail";
  const isVideo = asset.kind === "video_clip" || asset.kind === "final_video";
  const isAudio = asset.kind === "voice" || asset.kind === "music";

  return (
    <div className="card overflow-hidden p-0">
      <div className="flex aspect-video items-center justify-center bg-slate-100 dark:bg-slate-800">
        {isImage && url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={url} alt={asset.kind} className="h-full w-full object-cover" />
        ) : isVideo && url ? (
          <video src={url} controls className="h-full w-full object-cover" />
        ) : isAudio && url ? (
          <div className="flex w-full flex-col items-center gap-1 px-2">
            <span className="text-2xl">{KIND_ICONS[asset.kind] ?? "📄"}</span>
            <audio src={url} controls className="w-full max-w-[180px]" style={{ height: 28 }} />
          </div>
        ) : (
          <span className="text-3xl">{KIND_ICONS[asset.kind] ?? "📄"}</span>
        )}
      </div>
      <div className="p-3">
        <div className="flex items-center justify-between gap-2">
          <p className="truncate text-xs font-bold">
            {KIND_ICONS[asset.kind]} {asset.kind.replace("_", " ")}
            {asset.scene_index != null ? ` #${asset.scene_index}` : ""}
          </p>
          {asset.duration != null && (
            <span className="text-[10px] text-slate-400">{formatDuration(asset.duration)}</span>
          )}
        </div>
        <div className="mt-1.5 flex items-center justify-between">
          <span className="text-[10px] text-slate-400">{formatDate(asset.created_at)}</span>
          {url && (
            <a href={url} target="_blank" rel="noreferrer" download
              className="text-[11px] font-semibold text-brand-500 hover:underline">
              Download
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
