'use client'

import { IconBolt, IconGallery, IconImage, IconVideo } from './Icons'

export type TabId = 'image' | 'video' | 'gallery'

const TABS: { id: TabId; label: string; short: string; Icon: typeof IconImage }[] = [
  { id: 'image', label: 'Text to Image', short: 'Image', Icon: IconImage },
  { id: 'video', label: 'Image to Video', short: 'Video', Icon: IconVideo },
  { id: 'gallery', label: 'Gallery', short: 'Gallery', Icon: IconGallery },
]

export default function Header({
  tab,
  setTab,
  galleryCount,
}: {
  tab: TabId
  setTab: (t: TabId) => void
  galleryCount: number
}) {
  return (
    <header className="sticky top-0 z-50 border-b border-white/[0.07] bg-ink-950/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3 sm:px-6">
        <div className="flex min-w-0 items-center gap-2.5">
          <div className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 text-base shadow-lg shadow-brand-600/25">
            📦
          </div>
          <div className="min-w-0">
            <div className="truncate text-[15px] font-bold leading-tight tracking-tight text-white">
              Tiny Workers Studio
            </div>
            <div className="hidden text-[11px] leading-tight text-zinc-500 sm:block">
              Unlimited · No credits · No watermark
            </div>
          </div>
        </div>

        <nav className="no-scrollbar ml-auto flex items-center gap-1 overflow-x-auto rounded-xl border border-white/[0.07] bg-white/[0.03] p-1">
          {TABS.map(({ id, label, short, Icon }) => {
            const active = tab === id
            return (
              <button
                key={id}
                onClick={() => setTab(id)}
                aria-current={active ? 'page' : undefined}
                className={`relative flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-2 text-[13px] font-semibold transition-all ${
                  active ? 'bg-white/[0.10] text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-200'
                }`}
              >
                <Icon width={15} height={15} />
                <span className="hidden sm:inline">{label}</span>
                <span className="sm:hidden">{short}</span>
                {id === 'gallery' && galleryCount > 0 && (
                  <span className="ml-0.5 rounded-full bg-brand-500 px-1.5 py-px text-[10px] font-bold text-white">
                    {galleryCount}
                  </span>
                )}
              </button>
            )
          })}
        </nav>

        <div className="hidden shrink-0 items-center gap-1.5 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1.5 text-[11px] font-semibold text-emerald-300 lg:flex">
          <IconBolt width={12} height={12} />
          FREE FOREVER
        </div>
      </div>
    </header>
  )
}
