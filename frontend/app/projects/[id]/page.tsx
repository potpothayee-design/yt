"use client";

/** Project detail = Preview & approval center.
 * Review everything, edit the script, regenerate parts, and only then approve upload.
 */

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError, media } from "@/lib/api";
import type {
  Asset,
  ProjectDetail,
  Script,
  Scene,
  VideoMetadata,
} from "@/lib/types";
import { formatDuration } from "@/lib/utils";
import { Card, SectionTitle, Spinner, StatusBadge } from "@/components/ui";
import { ProgressTracker } from "@/components/ProgressTracker";
import { VideoPlayer } from "@/components/VideoPlayer";

type RegenTarget = "scene" | "thumbnail" | "voice" | "music" | "video";

export default function ProjectDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const projectId = Number(id);
  const router = useRouter();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [sceneIndex, setSceneIndex] = useState(0);
  const [showUpload, setShowUpload] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const deleteProject = async () => {
    if (!project) return;
    const name = project.title || project.topic;
    if (!window.confirm(`Delete "${name}" for good?\n\nThis removes the video, images, audio and all project data. This cannot be undone.`)) return;
    setDeleting(true);
    try {
      await api.delete(`/api/v1/projects/${project.id}`);
      router.replace("/projects");
    } catch {
      setError("Could not delete the project — please try again.");
      setDeleting(false);
    }
  };

  const refresh = useCallback(async () => {
    try {
      setProject(await api.get<ProjectDetail>(`/api/v1/projects/${projectId}`));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "failed to load project");
    }
  }, [projectId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // poll while work is in flight
  const active =
    project?.status === "generating" || project?.status === "uploading";
  useEffect(() => {
    if (!active) return;
    const timer = setInterval(refresh, 3000);
    return () => clearInterval(timer);
  }, [active, refresh]);

  const regenerate = async (target: RegenTarget) => {
    setBusy(target);
    setActionMsg(null);
    try {
      const body =
        target === "scene"
          ? { target, scene_index: sceneIndex }
          : { target };
      await api.post(`/api/v1/projects/${projectId}/regenerate`, body);
      setActionMsg(`regeneration started (${target}) — tracking progress below`);
      await refresh();
    } catch (err) {
      setActionMsg(err instanceof ApiError ? err.message : `failed to regenerate ${target}`);
    } finally {
      setBusy(null);
    }
  };

  const saveScript = async (script: Script) => {
    setBusy("script-save");
    try {
      await api.patch(`/api/v1/projects/${projectId}`, { script });
      setActionMsg("script saved — regenerate Voice (or the Entire Video) to apply it");
      await refresh();
    } catch (err) {
      setActionMsg(err instanceof ApiError ? err.message : "save failed");
    } finally {
      setBusy(null);
    }
  };

  const saveMetadata = async (metadata: VideoMetadata) => {
    setBusy("meta-save");
    try {
      await api.patch(`/api/v1/projects/${projectId}`, { video_metadata: metadata });
      setActionMsg("metadata saved");
      await refresh();
    } catch (err) {
      setActionMsg(err instanceof ApiError ? err.message : "save failed");
    } finally {
      setBusy(null);
    }
  };

  if (error) {
    return (
      <div className="mx-auto max-w-3xl">
        <Card>
          <p className="text-sm text-rose-500">{error}</p>
          <Link href="/projects" className="btn-secondary mt-4">
            ← Back to projects
          </Link>
        </Card>
      </div>
    );
  }
  if (!project) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner className="h-8 w-8 text-brand-500" />
      </div>
    );
  }

  const finalAsset = project.assets.find((a) => a.kind === "final_video");
  const thumbnails = project.assets.filter((a) => a.kind === "thumbnail");
  const captionAssets = project.assets.filter((a) => a.kind === "captions");

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      {/* header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link href="/projects" className="text-xs font-semibold text-brand-500 hover:underline">
            ← Projects
          </Link>
          <h1 className="mt-1 text-2xl font-extrabold">
            {project.title || project.topic}
          </h1>
          <div className="mt-1.5 flex items-center gap-2">
            <StatusBadge status={project.status} />
            {finalAsset?.duration != null && (
              <span className="text-xs text-slate-400">
                {formatDuration(finalAsset.duration)}
              </span>
            )}
            <span className="text-xs text-slate-400">
              {String(project.params?.target_age ?? "")} •{" "}
              {String(project.params?.aspect_ratio ?? "")} •{" "}
              {String(project.params?.style ?? "")}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {project.status === "ready_for_review" && (
            <button className="btn-approve px-5 py-3 text-base" onClick={() => setShowUpload(true)}>
              ✅ Approve Upload
            </button>
          )}
          <button
            type="button"
            onClick={deleteProject}
            disabled={deleting}
            title="Delete project and all its files"
            className="btn-secondary border-rose-300 px-4 py-3 text-rose-600 hover:bg-rose-50 disabled:opacity-50 dark:border-rose-900 dark:text-rose-400 dark:hover:bg-rose-950"
          >
            {deleting ? "Deleting…" : "🗑 Delete"}
          </button>
        </div>
      </div>

      {actionMsg && (
        <p className="rounded-xl bg-brand-500/10 p-3 text-sm text-brand-700 dark:text-brand-300">
          {actionMsg}
        </p>
      )}

      {/* generating view */}
      {project.status === "generating" && project.latest_job && (
        <ProgressTracker jobId={project.latest_job.id} projectStatus={project.status} />
      )}
      {project.status === "failed" && (
        <Card>
          <p className="text-sm font-semibold text-rose-500">{project.error}</p>
          <div className="mt-3 flex gap-2">
            <button
              className="btn-primary"
              disabled={busy === "video"}
              onClick={() => regenerate("video")}
            >
              {busy === "video" && <Spinner />} Retry Generation (resumes finished steps)
            </button>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* left: video + thumbnails + captions */}
        <div className="space-y-6 xl:col-span-2">
          <Card>
            <SectionTitle title="Video Preview" subtitle="Final polished edit with narration, music and burned-in captions" />
            <VideoPlayer
              src={project.final_video_url}
              poster={project.thumbnail_url}
            />
          </Card>

          <Card>
            <SectionTitle
              title="Thumbnails"
              subtitle="Concepts optimized for readability and click-through"
              action={
                <button
                  className="btn-secondary text-xs"
                  disabled={busy === "thumbnail"}
                  onClick={() => regenerate("thumbnail")}
                >
                  {busy === "thumbnail" && <Spinner className="mr-1" />} Regenerate Thumbnail
                </button>
              }
            />
            {thumbnails.length === 0 ? (
              <p className="py-4 text-center text-sm text-slate-400">No thumbnails yet.</p>
            ) : (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {thumbnails.map((t) => (
                  <a key={t.id} href={media(t.url) ?? "#"} target="_blank" rel="noreferrer">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={media(t.url) ?? ""}
                      alt={`thumbnail ${t.scene_index}`}
                      className="aspect-video w-full rounded-xl border border-slate-200 object-cover transition hover:scale-[1.02] dark:border-slate-700"
                    />
                  </a>
                ))}
              </div>
            )}
          </Card>

          <Card>
            <SectionTitle title="Captions & Music" />
            <div className="flex flex-wrap items-center gap-3 text-sm">
              {captionAssets.map((c) => (
                <a
                  key={c.id}
                  className="btn-secondary text-xs"
                  href={media(c.url) ?? "#"}
                  target="_blank"
                  rel="noreferrer"
                >
                  ⬇ Download {c.path.split("/").pop()}
                </a>
              ))}
              <span className="text-xs text-slate-500 dark:text-slate-400">
                🎵 {project.video_metadata?.music_credits ?? "music credits appear after generation"}
              </span>
            </div>
            <p className="mt-2 text-xs text-slate-400">
              Burned-in animated captions with word highlighting are already included
              in the video; SRT and ASS files are provided for YouTube's caption uploader.
            </p>
          </Card>

          {project.script && (
            <ScriptEditor
              script={project.script}
              assets={project.assets}
              onSave={saveScript}
              saving={busy === "script-save"}
              disabled={active}
            />
          )}

          {project.storyboard && <StoryboardView rows={project.storyboard} />}

          {project.prompts && (
            <Card>
              <SectionTitle title="Scene Prompts & Character Sheet"
                subtitle="Consistency contract used for every scene render" />
              <p className="text-sm">
                Mascot: <b>{project.prompts.character_sheet?.name}</b> — body{" "}
                <span
                  className="inline-block h-3 w-3 rounded-full align-middle"
                  style={{ background: project.prompts.character_sheet?.body_hex }}
                />{" "}
                {project.prompts.character_sheet?.body_hex}, accessory:{" "}
                {project.prompts.character_sheet?.accessory}
              </p>
              <details className="mt-3 text-sm">
                <summary className="cursor-pointer font-semibold text-brand-500">
                  Show prompts ({project.prompts.scenes?.length ?? 0} scenes)
                </summary>
                <div className="mt-2 max-h-72 space-y-3 overflow-y-auto nice-scroll pr-1">
                  {project.prompts.scenes?.map((s, i) => (
                    <div key={i} className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800/60">
                      <p className="text-xs font-bold uppercase text-slate-400">image prompt — scene {i}</p>
                      <p className="mt-1 text-xs">{s.image_prompt}</p>
                      <p className="mt-2 text-xs font-bold uppercase text-slate-400">video prompt</p>
                      <p className="mt-1 text-xs">{s.video_prompt}</p>
                    </div>
                  ))}
                  <div className="rounded-xl bg-rose-500/5 p-3">
                    <p className="text-xs font-bold uppercase text-rose-400">negative prompt</p>
                    <p className="mt-1 text-xs">{project.prompts.negative_prompt}</p>
                  </div>
                </div>
              </details>
            </Card>
          )}
        </div>

        {/* right column: metadata + regeneration actions */}
        <div className="space-y-6">
          <MetadataEditor
            metadata={project.video_metadata}
            fallbackTitle={project.title || project.topic}
            onSave={saveMetadata}
            saving={busy === "meta-save"}
          />

          <Card>
            <SectionTitle title="Regeneration" subtitle="Fix anything, then approve" />
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <select
                  className="input flex-1"
                  value={sceneIndex}
                  onChange={(e) => setSceneIndex(Number(e.target.value))}
                >
                  {(project.script?.scenes ?? []).map((s) => (
                    <option key={s.index} value={s.index}>
                      Scene {s.index + 1}: {s.on_screen_text || s.type}
                    </option>
                  ))}
                </select>
                <button
                  className="btn-secondary text-xs"
                  disabled={busy === "scene" || active}
                  onClick={() => regenerate("scene")}
                >
                  {busy === "scene" && <Spinner className="mr-1" />} Regenerate Scene
                </button>
              </div>
              <button className="btn-secondary w-full text-xs" disabled={busy === "voice" || active} onClick={() => regenerate("voice")}>
                {busy === "voice" && <Spinner className="mr-1" />} Regenerate Voice
              </button>
              <button className="btn-secondary w-full text-xs" disabled={busy === "music" || active} onClick={() => regenerate("music")}>
                {busy === "music" && <Spinner className="mr-1" />} Regenerate Music
              </button>
              <button className="btn-secondary w-full text-xs" disabled={busy === "video" || active} onClick={() => regenerate("video")}>
                {busy === "video" && <Spinner className="mr-1" />} Regenerate Entire Video
              </button>
              {project.status === "ready_for_review" && (
                <button className="btn-approve w-full" onClick={() => setShowUpload(true)}>
                  ✅ Approve Upload
                </button>
              )}
              <p className="text-xs text-slate-400">
                Nothing is ever published without pressing Approve Upload and
                confirming the upload dialog.
              </p>
            </div>
          </Card>

          {project.latest_job && project.latest_job.status !== "running" && (
            <Card>
              <SectionTitle title="Last Pipeline Run" />
              {project.latest_job.steps && (
                <ol className="space-y-1.5 text-xs">
                  {project.latest_job.steps.map((s) => (
                    <li key={s.name} className="flex items-center justify-between">
                      <span>{s.label}</span>
                      <span
                        className={
                          s.status === "done"
                            ? "text-emerald-500"
                            : s.status === "failed"
                              ? "text-rose-500"
                              : "text-slate-400"
                        }
                      >
                        {s.name === "upload" && s.status === "pending"
                          ? "Pending Approval"
                          : s.status}
                      </span>
                    </li>
                  ))}
                </ol>
              )}
            </Card>
          )}
        </div>
      </div>

      {showUpload && (
        <UploadDialog
          project={project}
          onClose={() => setShowUpload(false)}
          onStarted={async () => {
            setShowUpload(false);
            setActionMsg("upload started — watch status on the Uploads page or here");
            await refresh();
          }}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// script editor
// ---------------------------------------------------------------------------

function ScriptEditor({
  script,
  assets,
  onSave,
  saving,
  disabled,
}: {
  script: Script;
  assets: Asset[];
  onSave: (script: Script) => void;
  saving: boolean;
  disabled: boolean;
}) {
  const [scenes, setScenes] = useState<Scene[]>(script.scenes);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    setScenes(script.scenes);
    setDirty(false);
  }, [script]);

  const update = (index: number, narration: string) => {
    setScenes((prev) => prev.map((s) => (s.index === index ? { ...s, narration } : s)));
    setDirty(true);
  };

  const sceneImage = (index: number) => {
    const asset = assets.find((a) => a.kind === "image" && a.scene_index === index);
    return asset ? media(asset.url) : null;
  };

  return (
    <Card>
      <SectionTitle
        title="Script"
        subtitle="Edit narration per scene — then regenerate voice to apply"
        action={
          <button
            className="btn-primary text-xs"
            disabled={!dirty || saving || disabled}
            onClick={() => onSave({ ...script, scenes })}
          >
            {saving && <Spinner className="mr-1" />} Save Script
          </button>
        }
      />
      <div className="space-y-4">
        {scenes.map((scene) => (
          <div key={scene.index} className="flex gap-3 rounded-2xl bg-slate-50 p-3 dark:bg-slate-800/50">
            {sceneImage(scene.index) ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={sceneImage(scene.index) ?? ""}
                alt=""
                className="hidden h-20 w-32 rounded-xl object-cover sm:block"
              />
            ) : (
              <div className="hidden h-20 w-32 items-center justify-center rounded-xl bg-slate-200 text-xl dark:bg-slate-700 sm:flex">
                🎞️
              </div>
            )}
            <div className="min-w-0 flex-1">
              <div className="mb-1 flex items-center justify-between gap-2">
                <p className="text-xs font-bold uppercase tracking-wide text-slate-400">
                  {scene.type} • {scene.on_screen_text}
                </p>
                {scene.planned_duration && (
                  <span className="text-xs text-slate-400">
                    ~{scene.planned_duration.toFixed(1)}s
                  </span>
                )}
              </div>
              <textarea
                className="input min-h-[70px] resize-y text-sm"
                value={scene.narration}
                disabled={disabled}
                onChange={(e) => update(scene.index, e.target.value)}
              />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// storyboard view
// ---------------------------------------------------------------------------

function StoryboardView({ rows }: { rows: ProjectDetail["storyboard"] }) {
  if (!rows) return null;
  return (
    <Card>
      <SectionTitle title="Storyboard" subtitle="Scene-by-scene production plan" />
      <div className="nice-scroll overflow-x-auto">
        <table className="w-full min-w-[760px] text-left text-xs">
          <thead>
            <tr className="border-b border-slate-200 text-[11px] uppercase tracking-wide text-slate-400 dark:border-slate-700">
              <th className="py-2 pr-3">Scene</th>
              <th className="py-2 pr-3">Narration</th>
              <th className="py-2 pr-3">Visual</th>
              <th className="py-2 pr-3">Camera</th>
              <th className="py-2 pr-3">Animation</th>
              <th className="py-2">Duration</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.index} className="border-b border-slate-100 align-top dark:border-slate-800">
                <td className="py-2.5 pr-3 font-bold">{row.index + 1}</td>
                <td className="max-w-[220px] py-2.5 pr-3">{row.narration}</td>
                <td className="max-w-[200px] py-2.5 pr-3">{row.visual_description}</td>
                <td className="py-2.5 pr-3">{row.camera}</td>
                <td className="py-2.5 pr-3">{row.motion}</td>
                <td className="py-2.5">{row.planned_duration?.toFixed(1)}s</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// metadata editor
// ---------------------------------------------------------------------------

function MetadataEditor({
  metadata,
  fallbackTitle,
  onSave,
  saving,
}: {
  metadata: VideoMetadata | null;
  fallbackTitle: string;
  onSave: (metadata: VideoMetadata) => void;
  saving: boolean;
}) {
  const [title, setTitle] = useState(metadata?.title ?? fallbackTitle);
  const [description, setDescription] = useState(metadata?.description ?? "");
  const [tags, setTags] = useState((metadata?.tags ?? []).join(", "));

  useEffect(() => {
    setTitle(metadata?.title ?? fallbackTitle);
    setDescription(metadata?.description ?? "");
    setTags((metadata?.tags ?? []).join(", "));
  }, [metadata, fallbackTitle]);

  return (
    <Card>
      <SectionTitle title="YouTube Metadata" subtitle="SEO-optimized, kid-safe" />
      <div className="space-y-3">
        <div>
          <label className="label">Title</label>
          <input className="input" value={title} maxLength={100}
            onChange={(e) => setTitle(e.target.value)} />
          <p className="mt-1 text-right text-xs text-slate-400">{title.length}/100</p>
        </div>
        <div>
          <label className="label">Description</label>
          <textarea className="input min-h-[160px] resize-y text-xs"
            value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        <div>
          <label className="label">Tags (comma separated)</label>
          <textarea className="input min-h-[60px] resize-y text-xs"
            value={tags} onChange={(e) => setTags(e.target.value)} />
        </div>
        {metadata?.hashtags && (
          <div>
            <label className="label">Hashtags</label>
            <p className="text-sm text-brand-500">{metadata.hashtags.join("  ")}</p>
          </div>
        )}
        {metadata?.chapters && metadata.chapters.length > 0 && (
          <div>
            <label className="label">Chapters</label>
            <ul className="space-y-1 text-xs">
              {metadata.chapters.map((ch, i) => (
                <li key={i}>
                  <span className="font-mono text-slate-400">
                    {typeof ch.time === "number"
                      ? `${Math.floor(ch.time / 60)}:${String(Math.floor(ch.time % 60)).padStart(2, "0")}`
                      : ch.time || "—"}
                  </span>{" "}
                  {ch.label}
                </li>
              ))}
            </ul>
          </div>
        )}
        <p className="text-xs text-slate-400">
          👶 Audience: made for kids (auto-set). {metadata?.disclosure}
        </p>
        <button
          className="btn-primary w-full text-xs"
          disabled={saving}
          onClick={() =>
            onSave({
              ...(metadata ?? {}),
              title,
              description,
              tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
            })
          }
        >
          {saving && <Spinner className="mr-1" />} Save Metadata
        </button>
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// approve-upload dialog (explicit confirmation gate)
// ---------------------------------------------------------------------------

function UploadDialog({
  project,
  onClose,
  onStarted,
}: {
  project: ProjectDetail;
  onClose: () => void;
  onStarted: () => void;
}) {
  const metadata = project.video_metadata ?? {};
  const [privacy, setPrivacy] = useState<"private" | "unlisted" | "public">("private");
  const [madeForKids, setMadeForKids] = useState(true);
  const [scheduledAt, setScheduledAt] = useState("");
  const [title, setTitle] = useState(metadata.title ?? project.title ?? project.topic);
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ytConnected, setYtConnected] = useState<boolean | null>(null);

  useEffect(() => {
    api
      .get<{ configured: boolean; connected: boolean; channel: string }>(
        "/api/v1/youtube/status"
      )
      .then((s) => setYtConnected(s.connected))
      .catch(() => setYtConnected(false));
  }, []);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.post(`/api/v1/projects/${project.id}/uploads`, {
        confirm: true,
        privacy,
        made_for_kids: madeForKids,
        scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
        title,
      });
      onStarted();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "upload failed to start");
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      onClick={onClose}>
      <div className="card w-full max-w-lg p-6" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-extrabold">Approve Upload to YouTube</h2>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          The video will be uploaded to YOUR connected YouTube channel. Review the
          settings — nothing is automatic.
        </p>
        {ytConnected === false && (
          <p className="mt-3 rounded-xl bg-amber-500/10 p-3 text-sm text-amber-600 dark:text-amber-400">
            ⚠ YouTube is not connected yet. Connect your channel on the{" "}
            <Link href="/settings" className="font-semibold underline">
              Settings page
            </Link>{" "}
            first (OAuth login).
          </p>
        )}
        <div className="mt-4 space-y-4">
          <div>
            <label className="label">Video title</label>
            <input className="input" value={title} maxLength={100}
              onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div>
            <label className="label">Privacy</label>
            <select className="input" value={privacy}
              onChange={(e) => setPrivacy(e.target.value as typeof privacy)}>
              <option value="private">Private (saved as draft — recommended)</option>
              <option value="unlisted">Unlisted</option>
              <option value="public">Public</option>
            </select>
          </div>
          <div>
            <label className="label">Schedule publication (optional)</label>
            <input type="datetime-local" className="input" value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)} />
            {scheduledAt && (
              <p className="mt-1 text-xs text-slate-400">
                Uploaded as private and auto-published at the scheduled time.
              </p>
            )}
          </div>
          <label className="flex items-center gap-2.5 text-sm">
            <input type="checkbox" checked={madeForKids}
              onChange={(e) => setMadeForKids(e.target.checked)}
              className="h-4 w-4 accent-brand-500" />
            Made for kids (COPPA audience setting)
          </label>
          <label className="flex items-start gap-2.5 rounded-xl bg-emerald-500/10 p-3 text-sm">
            <input type="checkbox" checked={confirm}
              onChange={(e) => setConfirm(e.target.checked)}
              className="mt-0.5 h-4 w-4 accent-emerald-500" />
            <span>
              <b>I approve this upload.</b> I reviewed the video, script, thumbnail
              and metadata, and I confirm this content is original and appropriate
              for children.
            </span>
          </label>
          {error && (
            <p className="rounded-xl bg-rose-500/10 p-3 text-sm text-rose-600 dark:text-rose-400">
              {error}
            </p>
          )}
          <div className="flex gap-2">
            <button className="btn-secondary flex-1" onClick={onClose} disabled={busy}>
              Cancel
            </button>
            <button className="btn-approve flex-1" onClick={submit}
              disabled={!confirm || busy || ytConnected !== true}>
              {busy && <Spinner />} Upload to YouTube
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
