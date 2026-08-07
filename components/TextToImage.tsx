'use client'

import { useCallback, useRef, useState } from 'react'
import { ASPECTS, ASPECT_MAP, STYLES, type AspectId, type StyleId } from '@/lib/styles'
import { fetchImageBlob, randomSeed } from '@/lib/pollinations'
import { downloadBlob, slugify, upscaleToBlob, copyText } from '@/lib/download'
import type { GalleryItem } from '@/lib/types'
import {
  IconCheck,
  IconCopy,
  IconDice,
  IconDownload,
  IconLayers,
  IconRefresh,
  IconSparkles,
  IconVideo,
} from './Icons'
import { useToast } from './Toast'

interface Result {
  id: string
  url: string
  blob: Blob
  finalPrompt: string
  seed: number
  model: string
  /** True when we only have a remote URL (no local pixel data). */
  remote?: boolean
}

export default function TextToImage({
  prompt,
  setPrompt,
  style,
  setStyle,
  aspect,
  setAspect,
  onSaved,
  onAnimate,
}: {
  prompt: string
  setPrompt: (v: string) => void
  style: StyleId
  setStyle: (v: StyleId) => void
  aspect: AspectId
  setAspect: (v: AspectId) => void
  onSaved: (item: GalleryItem, blob: Blob) => void
  onAnimate: (url: string, prompt: string, aspect: AspectId) => void
}) {
  const [count, setCount] = useState(1)
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState('')
  const [results, setResults] = useState<Result[]>([])
  const [copied, setCopied] = useState(false)
  const [exporting, setExporting] = useState<string | null>(null)
  const [remoteNotice, setItemsRemoteNotice] = useState(false)
  const abortRef = useRef(false)
  const toast = useToast()

  const ratioClass = ASPECT_MAP[aspect].ratioClass

  const generate = useCallback(async () => {
    if (!prompt.trim()) {
      toast('Write a prompt first — or tap a viral preset.', 'error')
      return
    }
    setBusy(true)
    abortRef.current = false
    setResults([])

    const made: Result[] = []
    try {
      for (let i = 0; i < count; i++) {
        if (abortRef.current) break
        setStatus(count > 1 ? `Rendering image ${i + 1} of ${count}…` : 'Rendering your scene…')
        const { blob, finalPrompt, width, height, model, seed, remoteUrl } = await fetchImageBlob(
          { prompt, style, aspect, seed: randomSeed() },
          {
            onAttempt: (m, attempt) =>
              setStatus(
                attempt > 1
                  ? `Engine busy — retrying on "${m}"…`
                  : count > 1
                    ? `Rendering image ${i + 1} of ${count}…`
                    : 'Rendering your scene…',
              ),
          },
        )
        const id = `img_${Date.now()}_${i}`
        const url = remoteUrl ?? URL.createObjectURL(blob)
        const r: Result = { id, url, blob, finalPrompt, seed, model, remote: Boolean(remoteUrl) }
        made.push(r)
        setResults((prev) => [...prev, r])

        const item: GalleryItem = {
          id,
          kind: 'image',
          url,
          mime: blob.type || 'image/jpeg',
          prompt: finalPrompt,
          rawPrompt: prompt,
          style,
          aspect,
          engine: `pollinations:${model}`,
          seed,
          width,
          height,
          createdAt: Date.now(),
        }
        // Only persist real pixel data; a remote-only result can't be stored.
        if (!remoteUrl) onSaved(item, blob)
        else setItemsRemoteNotice(true)
      }
      if (made.length) toast(`${made.length} image${made.length > 1 ? 's' : ''} ready — saved to gallery`, 'success')
    } catch (err) {
      toast(err instanceof Error ? err.message : 'Generation failed. Try again — it is always free.', 'error')
    } finally {
      setBusy(false)
      setStatus('')
    }
  }, [prompt, style, aspect, count, onSaved, toast])

  const handleDownload = async (r: Result) => {
    setExporting(r.id)
    try {
      const png = await upscaleToBlob(r.remote ? r.url : r.blob, aspect, 'image/png')
      const { width, height } = ASPECT_MAP[aspect]
      downloadBlob(png, `${slugify(prompt)}-${width}x${height}.png`)
      toast(`Downloaded 4K PNG (${width}×${height})`, 'success')
    } catch {
      if (r.remote) {
        // Can't touch the pixels — open it so the user can save it manually.
        window.open(r.url, '_blank', 'noopener,noreferrer')
        toast('Opened in a new tab — long-press or right-click to save', 'info')
      } else {
        downloadBlob(r.blob, `${slugify(prompt)}.jpg`)
        toast('Downloaded original resolution', 'info')
      }
    } finally {
      setExporting(null)
    }
  }

  const handleCopyPrompt = async () => {
    const ok = await copyText(prompt)
    if (ok) {
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
      toast('Prompt copied', 'success')
    }
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,380px)_minmax(0,1fr)]">
      {/* ---------------- Controls ---------------- */}
      <div className="card space-y-5 p-4 sm:p-5">
        <div>
          <div className="label">
            <IconSparkles width={12} height={12} />
            Prompt
          </div>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={6}
            placeholder="Tiny workers in hi-vis vests assembling a cardboard Ferrari, sparks flying, golden hour light…"
            className="field resize-y leading-relaxed"
          />
          <div className="mt-2 flex items-center justify-between gap-2">
            <span className="text-[11px] text-zinc-600">{prompt.length} characters</span>
            <button onClick={handleCopyPrompt} className="btn-ghost btn-sm" disabled={!prompt}>
              {copied ? (
                <IconCheck width={12} height={12} className="text-emerald-400" />
              ) : (
                <IconCopy width={12} height={12} />
              )}
              Copy
            </button>
          </div>
        </div>

        <div>
          <div className="label">
            <IconLayers width={12} height={12} />
            Style
          </div>
          <div className="grid gap-2">
            {STYLES.map((s) => {
              const active = style === s.id
              return (
                <button
                  key={s.id}
                  onClick={() => setStyle(s.id)}
                  className={`flex items-center gap-3 rounded-xl border p-3 text-left transition-all ${
                    active
                      ? 'border-brand-500/60 bg-brand-500/10 shadow-lg shadow-brand-600/10'
                      : 'border-white/10 bg-white/[0.02] hover:border-white/25 hover:bg-white/[0.05]'
                  }`}
                >
                  <span
                    className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-gradient-to-br text-base ${s.swatch}`}
                  >
                    {s.emoji}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[13px] font-semibold text-zinc-100">{s.name}</span>
                    <span className="block truncate text-[11px] text-zinc-500">
                      {s.id === 'photoreal'
                        ? 'Macro realism · tilt-shift diorama'
                        : s.id === 'pixar'
                          ? 'Emotional 3D animation still'
                          : 'Corrugated papercraft build'}
                    </span>
                  </span>
                  <span
                    className={`grid h-4 w-4 shrink-0 place-items-center rounded-full border ${
                      active ? 'border-brand-400 bg-brand-500' : 'border-white/25'
                    }`}
                  >
                    {active && <IconCheck width={9} height={9} className="text-white" />}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="label">Aspect</div>
            <div className="grid gap-1.5">
              {ASPECTS.map((a) => {
                const active = aspect === a.id
                return (
                  <button
                    key={a.id}
                    onClick={() => setAspect(a.id)}
                    className={`flex items-center gap-2 rounded-lg border px-2.5 py-2 text-left transition-all ${
                      active
                        ? 'border-brand-500/60 bg-brand-500/10'
                        : 'border-white/10 bg-white/[0.02] hover:border-white/25'
                    }`}
                  >
                    <span
                      className={`shrink-0 rounded-sm border-2 ${active ? 'border-brand-400' : 'border-zinc-600'}`}
                      style={{
                        width: a.id === '16:9' ? 18 : a.id === '9:16' ? 9 : 14,
                        height: a.id === '16:9' ? 10 : a.id === '9:16' ? 16 : 14,
                      }}
                    />
                    <span className="min-w-0">
                      <span className="block text-[12px] font-semibold text-zinc-200">{a.label}</span>
                      <span className="block truncate text-[10px] text-zinc-600">{a.hint}</span>
                    </span>
                  </button>
                )
              })}
            </div>
          </div>

          <div>
            <div className="label">Batch</div>
            <div className="grid grid-cols-2 gap-1.5">
              {[1, 2, 3, 4].map((n) => (
                <button
                  key={n}
                  onClick={() => setCount(n)}
                  className={`rounded-lg border py-2 text-[13px] font-semibold transition-all ${
                    count === n
                      ? 'border-brand-500/60 bg-brand-500/10 text-white'
                      : 'border-white/10 bg-white/[0.02] text-zinc-400 hover:border-white/25'
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
            <p className="mt-2 text-[10.5px] leading-relaxed text-zinc-600">
              Unlimited generations. Nothing is metered — batch as much as you like.
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <button onClick={generate} disabled={busy} className="btn-primary flex-1 py-3">
            {busy ? (
              <>
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                Generating…
              </>
            ) : (
              <>
                <IconSparkles width={15} height={15} />
                Generate {count > 1 ? `${count} images` : 'image'}
              </>
            )}
          </button>
          {busy ? (
            <button
              onClick={() => {
                abortRef.current = true
                toast('Stopping after the current image…', 'info')
              }}
              className="btn-ghost"
            >
              Stop
            </button>
          ) : (
            <button onClick={generate} disabled={!prompt} className="btn-ghost" title="Reroll with a new seed">
              <IconDice width={15} height={15} />
            </button>
          )}
        </div>

        <p className="rounded-lg border border-white/[0.07] bg-black/25 p-2.5 text-[10.5px] leading-relaxed text-zinc-600">
          Renders via <span className="text-zinc-400">Pollinations (Flux)</span> — free, keyless, unlimited. Exports are
          upscaled to true 4K PNG in your browser. Nothing is uploaded to us; there is no server in the loop.
        </p>
      </div>

      {/* ---------------- Canvas ---------------- */}
      <div className="space-y-4">
        {busy && results.length === 0 && (
          <div className={`card shimmer grid ${ratioClass} w-full max-w-md place-items-center`}>
            <div className="space-y-2 text-center">
              <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-brand-500/30 border-t-brand-500" />
              <p className="text-xs text-zinc-400">{status || 'Warming up the workshop…'}</p>
              <p className="text-[10px] text-zinc-600">First render can take 15–40s</p>
            </div>
          </div>
        )}

        {results.length === 0 && !busy && (
          <div className={`card grid ${ratioClass} w-full max-w-md place-items-center border-dashed`}>
            <div className="space-y-2 px-6 text-center">
              <div className="animate-floaty text-4xl">📦</div>
              <p className="text-sm font-semibold text-zinc-300">Your render appears here</p>
              <p className="text-[11px] leading-relaxed text-zinc-600">
                Pick a style and hit generate — or load one of the 7 viral presets below.
              </p>
            </div>
          </div>
        )}

        {remoteNotice && (
          <p className="rounded-lg border border-amber-500/25 bg-amber-500/10 p-2.5 text-[11px] leading-relaxed text-amber-200">
            Your browser blocked direct pixel access for some renders, so they&apos;re shown straight from the source.
            They still display and download, but can&apos;t be saved to the gallery or animated. Reloading the page
            usually clears this.
          </p>
        )}

        {results.length > 0 && (
          <div className={`grid gap-3 ${results.length > 1 ? 'sm:grid-cols-2' : 'max-w-md'}`}>
            {results.map((r) => (
              <figure key={r.id} className="card animate-fadeup overflow-hidden">
                <div className={`relative ${ratioClass} w-full overflow-hidden bg-black`}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={r.url} alt={prompt} className="h-full w-full object-cover" />
                </div>
                <figcaption className="flex flex-wrap items-center gap-1.5 p-2.5">
                  <button
                    onClick={() => handleDownload(r)}
                    disabled={exporting === r.id}
                    className="btn-primary btn-sm flex-1"
                  >
                    {exporting === r.id ? (
                      <>
                        <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                        4K…
                      </>
                    ) : (
                      <>
                        <IconDownload width={13} height={13} />
                        4K PNG
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => {
                      if (r.remote) {
                        toast('This render can\u2019t be animated — regenerate it first.', 'error')
                        return
                      }
                      onAnimate(r.url, prompt, aspect)
                    }}
                    className="btn-ghost btn-sm"
                    title="Animate this image"
                  >
                    <IconVideo width={13} height={13} />
                    Animate
                  </button>
                  <button
                    onClick={async () => {
                      const ok = await copyText(r.finalPrompt)
                      toast(ok ? 'Full prompt copied' : 'Copy failed', ok ? 'success' : 'error')
                    }}
                    className="btn-ghost btn-sm"
                    title="Copy the full expanded prompt"
                  >
                    <IconCopy width={13} height={13} />
                  </button>
                  <button onClick={generate} className="btn-ghost btn-sm" title="Reroll">
                    <IconRefresh width={13} height={13} />
                  </button>
                </figcaption>
              </figure>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
