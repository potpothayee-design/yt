'use client'

import { useMemo, useState } from 'react'
import type { GalleryItem } from '@/lib/types'
import { ASPECT_MAP } from '@/lib/styles'
import { copyText, downloadBlob, slugify, upscaleToBlob } from '@/lib/download'
import { getBlob } from '@/lib/storage'
import { IconCheck, IconCopy, IconDownload, IconTrash, IconClose } from './Icons'
import { useToast } from './Toast'

type Filter = 'all' | 'image' | 'video'

export default function Gallery({
  items,
  onDelete,
  onClear,
}: {
  items: GalleryItem[]
  onDelete: (id: string) => void
  onClear: () => void
}) {
  const [filter, setFilter] = useState<Filter>('all')
  const [copied, setCopied] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [lightbox, setLightbox] = useState<GalleryItem | null>(null)
  const toast = useToast()

  const filtered = useMemo(
    () => (filter === 'all' ? items : items.filter((i) => i.kind === filter)),
    [items, filter],
  )

  const handleCopy = async (item: GalleryItem) => {
    const ok = await copyText(item.rawPrompt || item.prompt)
    if (ok) {
      setCopied(item.id)
      setTimeout(() => setCopied((c) => (c === item.id ? null : c)), 1600)
      toast('Prompt copied', 'success')
    }
  }

  const handleDownload = async (item: GalleryItem) => {
    setBusy(item.id)
    try {
      const blob = (await getBlob(item.id)) ?? (await (await fetch(item.url)).blob())
      if (item.kind === 'video') {
        const ext = item.mime.includes('mp4') ? 'mp4' : 'webm'
        downloadBlob(blob, `${slugify(item.rawPrompt || item.prompt)}.${ext}`)
        toast(`Downloaded ${ext.toUpperCase()}`, 'success')
      } else {
        const png = await upscaleToBlob(blob, item.aspect, 'image/png')
        const { width, height } = ASPECT_MAP[item.aspect]
        downloadBlob(png, `${slugify(item.rawPrompt || item.prompt)}-${width}x${height}.png`)
        toast(`Downloaded 4K PNG (${width}×${height})`, 'success')
      }
    } catch {
      toast('Download failed — try regenerating this item', 'error')
    } finally {
      setBusy(null)
    }
  }

  if (!items.length) {
    return (
      <div className="card grid min-h-[50vh] place-items-center border-dashed p-10">
        <div className="max-w-xs space-y-2 text-center">
          <div className="animate-floaty text-5xl">🗂️</div>
          <p className="text-sm font-semibold text-zinc-300">Gallery is empty</p>
          <p className="text-[11.5px] leading-relaxed text-zinc-600">
            Everything you generate is saved here on your own device — it survives refreshes and never expires.
          </p>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex gap-1 rounded-xl border border-white/[0.07] bg-white/[0.03] p-1">
            {(['all', 'image', 'video'] as Filter[]).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`rounded-lg px-3 py-1.5 text-[12px] font-semibold capitalize transition ${
                  filter === f ? 'bg-white/[0.10] text-white' : 'text-zinc-500 hover:text-zinc-200'
                }`}
              >
                {f === 'all' ? 'All' : `${f}s`}
                <span className="ml-1.5 text-[10px] text-zinc-600">
                  {f === 'all' ? items.length : items.filter((i) => i.kind === f).length}
                </span>
              </button>
            ))}
          </div>
          <button
            onClick={() => {
              if (confirm('Delete every item in your gallery? This cannot be undone.')) onClear()
            }}
            className="btn-ghost btn-sm ml-auto text-red-300 hover:border-red-500/40 hover:bg-red-500/10"
          >
            <IconTrash width={12} height={12} />
            Clear all
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {filtered.map((item) => (
            <article key={item.id} className="card group animate-fadeup overflow-hidden">
              <button
                onClick={() => setLightbox(item)}
                className={`relative block w-full ${ASPECT_MAP[item.aspect].ratioClass} overflow-hidden bg-black`}
              >
                {item.kind === 'video' ? (
                  <video src={item.url} muted loop playsInline className="h-full w-full object-cover"
                    onMouseEnter={(e) => void (e.currentTarget as HTMLVideoElement).play().catch(() => {})}
                    onMouseLeave={(e) => (e.currentTarget as HTMLVideoElement).pause()}
                  />
                ) : (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={item.url} alt={item.rawPrompt} loading="lazy" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-[1.04]" />
                )}
                <span className="absolute left-1.5 top-1.5 rounded-md bg-black/70 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-white backdrop-blur">
                  {item.kind === 'video' ? `▶ ${item.durationSec}s` : item.aspect}
                </span>
              </button>

              <div className="space-y-2 p-2.5">
                <p className="line-clamp-2 text-[11px] leading-snug text-zinc-400">{item.rawPrompt || item.prompt}</p>
                <div className="flex gap-1.5">
                  <button
                    onClick={() => handleDownload(item)}
                    disabled={busy === item.id}
                    className="btn-primary btn-sm flex-1 !px-2"
                  >
                    {busy === item.id ? (
                      <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    ) : (
                      <>
                        <IconDownload width={12} height={12} />
                        {item.kind === 'video' ? 'MP4' : 'PNG'}
                      </>
                    )}
                  </button>
                  <button onClick={() => handleCopy(item)} className="btn-ghost btn-sm !px-2" title="Copy prompt">
                    {copied === item.id ? (
                      <IconCheck width={12} height={12} className="text-emerald-400" />
                    ) : (
                      <IconCopy width={12} height={12} />
                    )}
                  </button>
                  <button
                    onClick={() => onDelete(item.id)}
                    className="btn-ghost btn-sm !px-2 text-red-300 hover:border-red-500/40 hover:bg-red-500/10"
                    title="Delete"
                  >
                    <IconTrash width={12} height={12} />
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>

      {lightbox && (
        <div
          className="fixed inset-0 z-[90] grid place-items-center bg-black/90 p-4 backdrop-blur-sm"
          onClick={() => setLightbox(null)}
        >
          <button
            onClick={() => setLightbox(null)}
            className="absolute right-4 top-4 grid h-10 w-10 place-items-center rounded-full border border-white/15 bg-white/[0.06] text-white transition hover:bg-white/[0.14]"
            aria-label="Close"
          >
            <IconClose />
          </button>
          <div className="max-h-[88vh] w-full max-w-3xl space-y-3" onClick={(e) => e.stopPropagation()}>
            <div className="overflow-hidden rounded-2xl border border-white/10 bg-black">
              {lightbox.kind === 'video' ? (
                <video src={lightbox.url} controls autoPlay loop className="max-h-[70vh] w-full object-contain" />
              ) : (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={lightbox.url} alt={lightbox.rawPrompt} className="max-h-[70vh] w-full object-contain" />
              )}
            </div>
            <div className="card space-y-2.5 p-3.5">
              <p className="text-[12px] leading-relaxed text-zinc-300">{lightbox.rawPrompt || lightbox.prompt}</p>
              <div className="flex flex-wrap gap-1.5">
                <span className="chip">{lightbox.aspect}</span>
                <span className="chip">{lightbox.engine}</span>
                {lightbox.seed !== undefined && <span className="chip">seed {lightbox.seed}</span>}
                <span className="chip">{new Date(lightbox.createdAt).toLocaleString()}</span>
              </div>
              <div className="flex gap-1.5">
                <button onClick={() => handleDownload(lightbox)} className="btn-primary btn-sm">
                  <IconDownload width={13} height={13} />
                  Download {lightbox.kind === 'video' ? 'video' : '4K PNG'}
                </button>
                <button onClick={() => handleCopy(lightbox)} className="btn-ghost btn-sm">
                  <IconCopy width={13} height={13} />
                  Copy prompt
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
