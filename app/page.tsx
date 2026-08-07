'use client'

import { useCallback, useEffect, useState } from 'react'
import Header, { type TabId } from '@/components/Header'
import PresetGrid from '@/components/PresetGrid'
import TextToImage from '@/components/TextToImage'
import ImageToVideo from '@/components/ImageToVideo'
import GalleryView from '@/components/Gallery'
import { ToastProvider } from '@/components/Toast'
import type { GalleryItem } from '@/lib/types'
import type { AspectId, StyleId } from '@/lib/styles'
import type { PromptPreset } from '@/lib/presets'
import { clearAssets, deleteAsset, loadAssets, saveAsset } from '@/lib/storage'
import { IconBolt } from '@/components/Icons'

function Studio() {
  const [tab, setTab] = useState<TabId>('image')
  const [prompt, setPrompt] = useState('')
  const [style, setStyle] = useState<StyleId>('photoreal')
  const [aspect, setAspect] = useState<AspectId>('9:16')
  const [items, setItems] = useState<GalleryItem[]>([])
  const [videoSeed, setVideoSeed] = useState<{ url: string; prompt: string; aspect: AspectId } | null>(null)

  useEffect(() => {
    loadAssets().then(setItems)
  }, [])

  const handleSaved = useCallback((item: GalleryItem, blob: Blob) => {
    setItems((prev) => [item, ...prev])
    void saveAsset(item, blob)
  }, [])

  const handleDelete = useCallback((id: string) => {
    setItems((prev) => prev.filter((i) => i.id !== id))
    void deleteAsset(id)
  }, [])

  const handleClear = useCallback(() => {
    setItems([])
    void clearAssets()
  }, [])

  const usePreset = useCallback((p: PromptPreset) => {
    setPrompt(p.prompt)
    setStyle(p.style)
    setAspect(p.aspect)
    setTab('image')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  const handleAnimate = useCallback((url: string, p: string, a: AspectId) => {
    setVideoSeed({ url, prompt: p, aspect: a })
    setTab('video')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  return (
    <>
      <Header tab={tab} setTab={setTab} galleryCount={items.length} />

      <main className="mx-auto max-w-7xl space-y-8 px-4 py-6 sm:px-6 sm:py-8">
        {tab === 'image' && (
          <>
            <section className="space-y-3 text-center">
              <div className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1.5 text-[11px] font-semibold text-emerald-300">
                <IconBolt width={12} height={12} />
                No credits · No watermark · No login · Unlimited
              </div>
              <h1 className="text-balance text-3xl font-black tracking-tight text-white sm:text-4xl lg:text-5xl">
                Tiny Workers, Cardboard Puzzles
                <span className="block bg-gradient-to-r from-brand-300 via-brand-400 to-amber-200 bg-clip-text text-transparent">
                  & Pixar magic — for free
                </span>
              </h1>
              <p className="mx-auto max-w-xl text-pretty text-[13px] leading-relaxed text-zinc-400 sm:text-sm">
                Generate 4K vertical Shorts frames and cinematic video clips in seconds. Everything runs on free,
                keyless engines and inside your own browser, so it can never run out of credits.
              </p>
            </section>

            <TextToImage
              prompt={prompt}
              setPrompt={setPrompt}
              style={style}
              setStyle={setStyle}
              aspect={aspect}
              setAspect={setAspect}
              onSaved={handleSaved}
              onAnimate={handleAnimate}
            />

            <PresetGrid onUse={usePreset} />
          </>
        )}

        {tab === 'video' && (
          <>
            <section className="space-y-1.5">
              <h1 className="text-2xl font-black tracking-tight text-white sm:text-3xl">Image to Video</h1>
              <p className="max-w-2xl text-[13px] leading-relaxed text-zinc-400">
                Turn any frame into a 5–8 second cinematic clip with real camera moves, film grain and fades. Renders
                locally — no queues, no cold starts, no credits.
              </p>
            </section>
            <ImageToVideo seed={videoSeed} clearSeed={() => setVideoSeed(null)} onSaved={handleSaved} />
            <PresetGrid onUse={usePreset} />
          </>
        )}

        {tab === 'gallery' && (
          <>
            <section className="space-y-1.5">
              <h1 className="text-2xl font-black tracking-tight text-white sm:text-3xl">Gallery</h1>
              <p className="max-w-2xl text-[13px] leading-relaxed text-zinc-400">
                Saved privately on this device. Download 4K PNGs or MP4 clips, or copy any prompt to reuse it.
              </p>
            </section>
            <GalleryView items={items} onDelete={handleDelete} onClear={handleClear} />
          </>
        )}
      </main>

      <footer className="mt-10 border-t border-white/[0.07] px-4 py-8 sm:px-6">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 text-[11.5px] text-zinc-600 sm:flex-row sm:items-center sm:justify-between">
          <p>
            <span className="font-semibold text-zinc-400">Tiny Workers Studio</span> — free forever. Images via
            Pollinations (Flux), video rendered in your browser.
          </p>
          <p>You own everything you create. Nothing is uploaded to a server of ours.</p>
        </div>
      </footer>
    </>
  )
}

export default function Page() {
  return (
    <ToastProvider>
      <Studio />
    </ToastProvider>
  )
}
