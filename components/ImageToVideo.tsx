'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { ASPECTS, ASPECT_MAP, STYLES, type AspectId, type StyleId } from '@/lib/styles'
import { fetchImageBlob, randomSeed } from '@/lib/pollinations'
import { MOTIONS, loadImage, renderVideo, supportsRecording, type MotionId } from '@/lib/video'
import { generateAiVideo } from '@/lib/aivideo'
import { downloadBlob, slugify } from '@/lib/download'
import type { GalleryItem } from '@/lib/types'
import { IconDownload, IconSparkles, IconUpload, IconVideo, IconClose, IconPlus, IconBolt } from './Icons'
import { useToast } from './Toast'

type Engine = 'ai' | 'camera'

interface Source {
  id: string
  url: string
  label: string
}

export default function ImageToVideo({
  seed,
  clearSeed,
  onSaved,
}: {
  seed: { url: string; prompt: string; aspect: AspectId } | null
  clearSeed: () => void
  onSaved: (item: GalleryItem, blob: Blob) => void
}) {
  const [sources, setSources] = useState<Source[]>([])
  const [motionPrompt, setMotionPrompt] = useState('')
  const [motion, setMotion] = useState<MotionId>('push-in')
  const [duration, setDuration] = useState(6)
  const [aspect, setAspect] = useState<AspectId>('9:16')
  const [busy, setBusy] = useState(false)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState('')
  const [result, setResult] = useState<{ url: string; blob: Blob; ext: string; engine: string } | null>(null)
  const [engine, setEngine] = useState<Engine>('ai')
  const [canRecord, setCanRecord] = useState(true)
  const [genStyle, setGenStyle] = useState<StyleId>('photoreal')
  const fileRef = useRef<HTMLInputElement>(null)
  const toast = useToast()

  useEffect(() => setCanRecord(supportsRecording()), [])

  // Receive an image handed over from the Text-to-Image tab.
  useEffect(() => {
    if (!seed) return
    setSources([{ id: `seed_${Date.now()}`, url: seed.url, label: 'From generator' }])
    setAspect(seed.aspect)
    if (!motionPrompt) setMotionPrompt(seed.prompt)
    clearSeed()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seed])

  const addFiles = (files: FileList | null) => {
    if (!files?.length) return
    const next: Source[] = []
    Array.from(files)
      .slice(0, 4)
      .forEach((f, i) => {
        if (!f.type.startsWith('image/')) return
        next.push({ id: `up_${Date.now()}_${i}`, url: URL.createObjectURL(f), label: f.name })
      })
    if (!next.length) {
      toast('Please choose image files (PNG or JPG).', 'error')
      return
    }
    setSources((s) => [...s, ...next].slice(0, 4))
  }

  /** Generate a keyframe straight from text, so video works without an upload. */
  const generateKeyframe = useCallback(async () => {
    if (!motionPrompt.trim()) {
      toast('Describe the scene first, then generate a keyframe.', 'error')
      return
    }
    setBusy(true)
    setStatus('Generating keyframe…')
    try {
      const { blob, remoteUrl } = await fetchImageBlob({
        prompt: motionPrompt,
        style: genStyle,
        aspect,
        seed: randomSeed(),
      })
      if (remoteUrl) {
        // Without local pixel data the canvas would be tainted and the
        // recording would fail silently — better to say so up front.
        toast('Your browser blocked pixel access for this render, so it can\u2019t be animated. Try again.', 'error')
        return
      }
      setSources((s) =>
        [...s, { id: `gen_${Date.now()}`, url: URL.createObjectURL(blob), label: 'AI keyframe' }].slice(0, 4),
      )
      toast('Keyframe added', 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Keyframe generation failed', 'error')
    } finally {
      setBusy(false)
      setStatus('')
    }
  }, [motionPrompt, genStyle, aspect, toast])

  const render = useCallback(async () => {
    if (!sources.length) {
      toast('Add at least one image — upload one or generate a keyframe.', 'error')
      return
    }
    setBusy(true)
    setProgress(0)
    setStatus('Preparing…')
    setResult(null)

    const finish = (blob: Blob, mime: string, ext: string, engineTag: string, w: number, h: number) => {
      const url = URL.createObjectURL(blob)
      setResult({ url, blob, ext, engine: engineTag })
      const item: GalleryItem = {
        id: `vid_${Date.now()}`,
        kind: 'video',
        url,
        mime,
        prompt: motionPrompt || motion,
        rawPrompt: motionPrompt,
        style: null,
        aspect,
        engine: engineTag,
        width: w,
        height: h,
        durationSec: duration,
        createdAt: Date.now(),
      }
      onSaved(item, blob)
    }

    try {
      // ---- Path 1: real AI diffusion motion on free community GPUs ----
      if (engine === 'ai') {
        if (!motionPrompt.trim()) {
          toast('Describe the motion you want — the AI engine needs a prompt.', 'error')
          setBusy(false)
          return
        }
        try {
          const srcBlob = await (await fetch(sources[0].url)).blob()
          const out = await generateAiVideo({
            image: srcBlob,
            prompt: motionPrompt,
            durationSec: duration,
            aspect,
            onStatus: setStatus,
          })
          // Read the true output dimensions rather than storing 0x0.
          const dims = await new Promise<{ w: number; h: number }>((resolve) => {
            const v = document.createElement('video')
            v.preload = 'metadata'
            v.onloadedmetadata = () => resolve({ w: v.videoWidth, h: v.videoHeight })
            v.onerror = () => resolve({ w: 0, h: 0 })
            v.src = URL.createObjectURL(out.blob)
          })
          finish(out.blob, out.mime, out.ext, `${out.model} (free GPU)`, dims.w, dims.h)
          toast(`Real AI motion generated with ${out.model}`, 'success')
          return
        } catch (err) {
          if ((err as Error)?.name === 'AbortError') return
          // Never dead-end: fall through to the always-available renderer.
          toast('Free AI GPUs are busy — falling back to cinematic camera motion.', 'info')
          setStatus('Falling back to camera motion…')
        }
      }

      // ---- Path 2: guaranteed local canvas cinematography ----
      const imgs = await Promise.all(sources.map((s) => loadImage(s.url)))
      setStatus('Rendering cinematic motion…')
      const out = await renderVideo({
        images: imgs,
        aspect,
        durationSec: duration,
        motion,
        onProgress: setProgress,
      })
      finish(out.blob, out.mime, out.ext, `camera:${motion}`, out.width, out.height)
      toast(`Video ready — ${out.width}×${out.height} ${out.ext.toUpperCase()}`, 'success')
    } catch (err) {
      if ((err as Error)?.name === 'AbortError') return
      toast(err instanceof Error ? err.message : 'Render failed', 'error')
    } finally {
      setBusy(false)
      setStatus('')
    }
  }, [sources, aspect, duration, motion, motionPrompt, engine, onSaved, toast])

  const ratioClass = ASPECT_MAP[aspect].ratioClass

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,380px)_minmax(0,1fr)]">
      {/* ---------------- Controls ---------------- */}
      <div className="card space-y-5 p-4 sm:p-5">
        <div>
          <div className="label">
            <IconUpload width={12} height={12} />
            Source frames · {sources.length}/4
          </div>

          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault()
              addFiles(e.dataTransfer.files)
            }}
            onClick={() => fileRef.current?.click()}
            className="cursor-pointer rounded-xl border border-dashed border-white/15 bg-black/25 p-5 text-center transition hover:border-brand-500/50 hover:bg-brand-500/[0.04]"
          >
            <IconUpload width={20} height={20} className="mx-auto mb-1.5 text-zinc-500" />
            <p className="text-[12.5px] font-semibold text-zinc-300">Drop images or click to upload</p>
            <p className="mt-0.5 text-[10.5px] text-zinc-600">
              PNG / JPG · up to 4 frames for a multi-shot sequence
            </p>
          </div>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            multiple
            hidden
            onChange={(e) => {
              addFiles(e.target.files)
              e.target.value = ''
            }}
          />

          {sources.length > 0 && (
            <div className="mt-2.5 grid grid-cols-4 gap-1.5">
              {sources.map((s, i) => (
                <div key={s.id} className="group relative aspect-square overflow-hidden rounded-lg border border-white/10">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={s.url} alt={s.label} className="h-full w-full object-cover" />
                  <span className="absolute left-1 top-1 rounded bg-black/70 px-1 text-[9px] font-bold text-white">
                    {i + 1}
                  </span>
                  <button
                    onClick={() => setSources((arr) => arr.filter((x) => x.id !== s.id))}
                    className="absolute right-1 top-1 grid h-4 w-4 place-items-center rounded bg-black/70 text-white opacity-0 transition group-hover:opacity-100"
                    aria-label="Remove frame"
                  >
                    <IconClose width={9} height={9} />
                  </button>
                </div>
              ))}
              {sources.length < 4 && (
                <button
                  onClick={() => fileRef.current?.click()}
                  className="grid aspect-square place-items-center rounded-lg border border-dashed border-white/15 text-zinc-600 transition hover:border-brand-500/50 hover:text-brand-400"
                >
                  <IconPlus width={16} height={16} />
                </button>
              )}
            </div>
          )}
        </div>

        <div>
          <div className="label">Motion prompt</div>
          <textarea
            value={motionPrompt}
            onChange={(e) => setMotionPrompt(e.target.value)}
            rows={3}
            placeholder="Slow dolly in as the crane lowers the cardboard panel, dust drifting through sunlight…"
            className="field resize-y leading-relaxed"
          />
          <div className="mt-2 flex flex-wrap gap-1.5">
            <select
              value={genStyle}
              onChange={(e) => setGenStyle(e.target.value as StyleId)}
              className="field !w-auto !px-2 !py-1.5 !text-[11px]"
            >
              {STYLES.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.emoji} {s.short}
                </option>
              ))}
            </select>
            <button onClick={generateKeyframe} disabled={busy} className="btn-ghost btn-sm flex-1">
              <IconSparkles width={12} height={12} />
              Generate keyframe from text
            </button>
          </div>
        </div>

        <div>
          <div className="label">
            <IconBolt width={12} height={12} />
            Motion engine
          </div>
          <div className="grid gap-2">
            <button
              onClick={() => setEngine('ai')}
              className={`rounded-xl border p-3 text-left transition-all ${
                engine === 'ai'
                  ? 'border-brand-500/60 bg-brand-500/10'
                  : 'border-white/10 bg-white/[0.02] hover:border-white/25'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="text-[13px] font-semibold text-zinc-100">✨ Real AI motion</span>
                <span className="chip !text-[9px] !text-emerald-300">FREE</span>
              </div>
              <p className="mt-1 text-[10.5px] leading-relaxed text-zinc-500">
                True diffusion — objects and characters actually move. Runs Wan / LTX on free community GPUs.
                <span className="text-amber-300/90"> Queued: can take 1–8 min, and may be busy.</span> Falls back
                automatically.
              </p>
            </button>
            <button
              onClick={() => setEngine('camera')}
              className={`rounded-xl border p-3 text-left transition-all ${
                engine === 'camera'
                  ? 'border-brand-500/60 bg-brand-500/10'
                  : 'border-white/10 bg-white/[0.02] hover:border-white/25'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="text-[13px] font-semibold text-zinc-100">🎥 Cinematic camera</span>
                <span className="chip !text-[9px] !text-sky-300">INSTANT</span>
              </div>
              <p className="mt-1 text-[10.5px] leading-relaxed text-zinc-500">
                Camera moves over your frames, rendered locally in seconds. The subject itself doesn&apos;t move, but
                it never queues and never fails.
              </p>
            </button>
          </div>
        </div>

        <div className={engine === 'ai' ? 'opacity-40' : ''}>
          <div className="label">Camera move {engine === 'ai' && '· fallback only'}</div>
          <div className="grid grid-cols-2 gap-1.5">
            {MOTIONS.map((m) => (
              <button
                key={m.id}
                onClick={() => setMotion(m.id)}
                title={m.hint}
                className={`rounded-lg border px-2 py-2 text-[11.5px] font-semibold transition-all ${
                  motion === m.id
                    ? 'border-brand-500/60 bg-brand-500/10 text-white'
                    : 'border-white/10 bg-white/[0.02] text-zinc-400 hover:border-white/25'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="label">Duration · {duration}s</div>
            <input
              type="range"
              min={5}
              max={8}
              step={1}
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="w-full accent-brand-500"
            />
            <div className="mt-1 flex justify-between text-[10px] text-zinc-600">
              <span>5s</span>
              <span>8s</span>
            </div>
          </div>
          <div>
            <div className="label">Aspect</div>
            <div className="flex gap-1.5">
              {ASPECTS.map((a) => (
                <button
                  key={a.id}
                  onClick={() => setAspect(a.id)}
                  className={`flex-1 rounded-lg border py-2 text-[11.5px] font-semibold transition-all ${
                    aspect === a.id
                      ? 'border-brand-500/60 bg-brand-500/10 text-white'
                      : 'border-white/10 bg-white/[0.02] text-zinc-400 hover:border-white/25'
                  }`}
                >
                  {a.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <button onClick={render} disabled={busy || !sources.length} className="btn-primary w-full py-3">
          {busy ? (
            <>
              <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              {progress > 0 ? `Rendering ${progress}%` : status || 'Working…'}
            </>
          ) : (
            <>
              <IconVideo width={15} height={15} />
              {engine === 'ai' ? `Generate AI motion (${duration}s)` : `Render ${duration}s video`}
            </>
          )}
        </button>

        {engine === 'ai' && busy && (
          <p className="rounded-lg border border-amber-500/25 bg-amber-500/10 p-2.5 text-[10.5px] leading-relaxed text-amber-200">
            Waiting on a free shared GPU. This is the honest cost of free AI motion — there&apos;s no queue to skip
            without paying. Keep this tab open; if every engine is busy we&apos;ll render camera motion instead so you
            always get a clip.
          </p>
        )}

        {!canRecord && (
          <p className="rounded-lg border border-amber-500/25 bg-amber-500/10 p-2.5 text-[10.5px] leading-relaxed text-amber-200">
            This browser can&apos;t record canvas video. Use Chrome, Edge or Safari — or download stills and animate them
            in your editor.
          </p>
        )}

        <p className="rounded-lg border border-white/[0.07] bg-black/25 p-2.5 text-[10.5px] leading-relaxed text-zinc-600">
          Both engines are <span className="text-zinc-400">completely free with no credits and no account</span>. AI
          motion borrows free community GPUs (so it queues); camera motion renders on your own device (so it&apos;s
          instant). Between them you always get a clip.
        </p>
      </div>

      {/* ---------------- Preview ---------------- */}
      <div className="space-y-3">
        {busy && (
          <div className={`card grid ${ratioClass} w-full max-w-sm place-items-center`}>
            <div className="w-4/5 space-y-3 text-center">
              <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-brand-500/30 border-t-brand-500" />
              <p className="text-xs text-zinc-400">{status}</p>
              <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-brand-400 to-brand-600 transition-all duration-200"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-[10px] text-zinc-600">Rendering in real time — keep this tab visible</p>
            </div>
          </div>
        )}

        {!busy && result && (
          <figure className="card animate-fadeup max-w-sm overflow-hidden">
            <div className={`${ratioClass} w-full bg-black`}>
              <video src={result.url} controls autoPlay loop muted playsInline className="h-full w-full object-cover" />
            </div>
            <div className="border-b border-white/[0.07] px-2.5 py-1.5">
              <span className="chip !text-[10px]">{result.engine}</span>
            </div>
            <figcaption className="flex gap-1.5 p-2.5">
              <button
                onClick={() =>
                  downloadBlob(result.blob, `${slugify(motionPrompt || motion)}-${duration}s.${result.ext}`)
                }
                className="btn-primary btn-sm flex-1"
              >
                <IconDownload width={13} height={13} />
                Download {result.ext.toUpperCase()}
              </button>
              <button onClick={render} className="btn-ghost btn-sm">
                Re-render
              </button>
            </figcaption>
          </figure>
        )}

        {!busy && !result && (
          <div className={`card grid ${ratioClass} w-full max-w-sm place-items-center border-dashed`}>
            <div className="space-y-2 px-6 text-center">
              <div className="animate-floaty text-4xl">🎬</div>
              <p className="text-sm font-semibold text-zinc-300">Your video appears here</p>
              <p className="text-[11px] leading-relaxed text-zinc-600">
                Upload or generate a frame, pick a camera move, then render.
              </p>
            </div>
          </div>
        )}

        {sources.length > 1 && (
          <p className="max-w-sm text-[11px] leading-relaxed text-zinc-600">
            <span className="text-zinc-400">{sources.length} frames</span> will crossfade in order across the {duration}s
            timeline — perfect for build-up or before/after sequences.
          </p>
        )}
      </div>
    </div>
  )
}
