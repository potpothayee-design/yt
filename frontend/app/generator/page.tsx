"use client";

/** Video Generator: topic in → full production pipeline with live progress. */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Job, Project, TopicIdea } from "@/lib/types";
import { Card, Spinner } from "@/components/ui";
import { ProgressTracker } from "@/components/ProgressTracker";

const AGES = ["3-6", "7-9", "10-13"];
const STYLES = ["3D Cartoon", "2D Storybook", "Claymation", "Flat Design", "Watercolor"];
const ANIMATIONS = ["playful", "gentle", "bouncy", "calm"];
const VOICES = ["female", "male", "child"];
const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "es", label: "Spanish" },
  { code: "fr", label: "French" },
  { code: "de", label: "German" },
  { code: "pt", label: "Portuguese" },
  { code: "hi", label: "Hindi" },
];
const MOODS = ["cheerful", "calm", "adventure", "bedtime"];
const RATIOS = ["16:9", "9:16", "1:1"];
const QUALITIES = [
  { value: "draft", label: "Draft (fast preview)" },
  { value: "standard", label: "Standard (720p)" },
  { value: "high", label: "High (1080p)" },
];

export default function GeneratorPage() {
  const router = useRouter();
  const [topic, setTopic] = useState("");
  const [age, setAge] = useState("3-6");
  const [length, setLength] = useState(30);
  const [style, setStyle] = useState(STYLES[0]);
  const [animation, setAnimation] = useState(ANIMATIONS[0]);
  const [voice, setVoice] = useState(VOICES[0]);
  const [language, setLanguage] = useState("en");
  const [mood, setMood] = useState(MOODS[0]);
  const [ratio, setRatio] = useState("16:9");
  const [quality, setQuality] = useState("standard");
  const [runner, setRunner] = useState<"local" | "github">("local");

  const [ideas, setIdeas] = useState<TopicIdea[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [job, setJob] = useState<Job | null>(null);

  useEffect(() => {
    api.get<TopicIdea[]>("/api/v1/meta/topic-ideas").then(setIdeas).catch(() => {});
  }, []);

  // Watch generation: when it is ready, move to the preview page
  useEffect(() => {
    if (!project) return;
    if (project.status !== "generating") return;
    const timer = setInterval(async () => {
      try {
        const fresh = await api.get<Project>(`/api/v1/projects/${project.id}`);
        setProject(fresh);
        if (fresh.status === "ready_for_review") {
          clearInterval(timer);
          router.push(`/projects/${fresh.id}`);
        }
      } catch {
        /* transient */
      }
    }, 4000);
    return () => clearInterval(timer);
  }, [project, router]);

  const generate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) {
      setError("please enter a topic first");
      return;
    }
    setBusy(true);
    setError(null);
    setJob(null);
    try {
      const created = await api.post<Project>("/api/v1/projects", {
        topic: topic.trim(),
        params: {
          topic: topic.trim(),
          target_age: age,
          length_seconds: length,
          style,
          animation_type: animation,
          voice,
          language,
          music_mood: mood,
          aspect_ratio: ratio,
          quality,
        },
      });
      setProject(created);
      const started = await api.post<Job>(
        `/api/v1/projects/${created.id}/generate?runner=${runner}`
      );
      setJob(started);
      setProject(await api.get<Project>(`/api/v1/projects/${created.id}`));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "failed to start generation");
    } finally {
      setBusy(false);
    }
  };

  const generating = project?.status === "generating" && job;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold">Video Generator</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Type a topic — the studio researches, scripts, animates, narrates, scores
          and edits a complete kids video for your review.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <form onSubmit={generate} className="space-y-4">
            <div>
              <label className="label">Topic</label>
              <input
                className="input text-base"
                placeholder="e.g. ABCs, Dinosaurs, Solar System…"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                disabled={!!generating}
              />
              {ideas.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {ideas.slice(0, 9).map((idea) => (
                    <button
                      key={idea.topic}
                      type="button"
                      onClick={() => setTopic(idea.topic === "Any Topic!" ? "" : idea.topic)}
                      className="rounded-full bg-brand-500/10 px-2.5 py-1 text-xs font-semibold text-brand-600 transition hover:bg-brand-500/20 dark:text-brand-300"
                    >
                      {idea.topic}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Target Age</label>
                <select className="input" value={age} onChange={(e) => setAge(e.target.value)}>
                  {AGES.map((a) => (
                    <option key={a}>{a}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Video Length: {length}s</label>
                <input
                  type="range"
                  min={15}
                  max={300}
                  step={5}
                  value={length}
                  onChange={(e) => setLength(Number(e.target.value))}
                  className="mt-3 w-full accent-brand-500"
                />
              </div>
              <div>
                <label className="label">Style</label>
                <select className="input" value={style} onChange={(e) => setStyle(e.target.value)}>
                  {STYLES.map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Animation Type</label>
                <select className="input" value={animation} onChange={(e) => setAnimation(e.target.value)}>
                  {ANIMATIONS.map((a) => (
                    <option key={a}>{a}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Voice</label>
                <select className="input" value={voice} onChange={(e) => setVoice(e.target.value)}>
                  {VOICES.map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Language</label>
                <select className="input" value={language} onChange={(e) => setLanguage(e.target.value)}>
                  {LANGUAGES.map((l) => (
                    <option key={l.code} value={l.code}>
                      {l.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Music</label>
                <select className="input" value={mood} onChange={(e) => setMood(e.target.value)}>
                  {MOODS.map((m) => (
                    <option key={m}>{m}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Aspect Ratio</label>
                <select className="input" value={ratio} onChange={(e) => setRatio(e.target.value)}>
                  {RATIOS.map((r) => (
                    <option key={r}>{r}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Quality</label>
                <select className="input" value={quality} onChange={(e) => setQuality(e.target.value)}>
                  {QUALITIES.map((q) => (
                    <option key={q.value} value={q.value}>
                      {q.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Runner</label>
                <select
                  className="input"
                  value={runner}
                  onChange={(e) => setRunner(e.target.value as "local" | "github")}
                >
                  <option value="local">Local worker</option>
                  <option value="github">GitHub Actions (long jobs)</option>
                </select>
              </div>
            </div>

            {error && (
              <p className="rounded-xl bg-rose-500/10 p-3 text-sm text-rose-600 dark:text-rose-400">
                {error}
              </p>
            )}
            <button type="submit" className="btn-primary w-full py-3 text-base" disabled={busy || !!generating}>
              {busy || generating ? <Spinner /> : "✨"}
              {generating ? "Generating your video…" : "Generate Video"}
            </button>
            {generating && (
              <p className="text-center text-xs text-slate-400">
                You can safely leave this page — generation continues in the background.
              </p>
            )}
          </form>
        </Card>

        <div className="space-y-4">
          {generating && job ? (
            <>
              <ProgressTracker jobId={job.id} projectStatus={project?.status} />
              <Card>
                <h3 className="mb-2 text-sm font-bold">What happens next?</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  When the pipeline finishes you will be taken to the Preview page to
                  review the script, storyboard, thumbnail and the final video — and
                  only then approve the YouTube upload.
                </p>
              </Card>
            </>
          ) : (
            <Card className="flex h-full min-h-[320px] flex-col items-center justify-center text-center">
              <span className="text-5xl">🎬</span>
              <h3 className="mt-3 font-bold">Ready when you are</h3>
              <p className="mt-1 max-w-sm text-sm text-slate-500 dark:text-slate-400">
                Fill in the form and press <b>Generate Video</b>. The live pipeline
                tracker will show every step: research, script, storyboard, scene
                prompts, images, voice, video, music, captions, editing and preview.
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
