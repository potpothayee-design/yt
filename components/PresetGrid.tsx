'use client'

import { useState } from 'react'
import { PRESETS, type PromptPreset } from '@/lib/presets'
import { STYLE_MAP } from '@/lib/styles'
import { copyText } from '@/lib/download'
import { IconCheck, IconCopy, IconSparkles } from './Icons'
import { useToast } from './Toast'

export default function PresetGrid({ onUse }: { onUse: (p: PromptPreset) => void }) {
  const [copied, setCopied] = useState<string | null>(null)
  const toast = useToast()

  const handleCopy = async (p: PromptPreset) => {
    const ok = await copyText(p.prompt)
    if (ok) {
      setCopied(p.id)
      setTimeout(() => setCopied((c) => (c === p.id ? null : c)), 1600)
      toast('Prompt copied to clipboard', 'success')
    } else {
      toast('Could not copy — select the text manually', 'error')
    }
  }

  return (
    <section className="space-y-3">
      <div className="flex items-end justify-between gap-3">
        <div>
          <h2 className="flex items-center gap-2 text-sm font-bold text-white">
            <IconSparkles width={15} height={15} className="text-brand-400" />
            Viral Presets
          </h2>
          <p className="mt-0.5 text-xs text-zinc-500">
            Tap a card to load the full prompt, style and aspect ratio.
          </p>
        </div>
        <span className="chip shrink-0">{PRESETS.length} ready</span>
      </div>

      <div className="grid gap-2.5 sm:grid-cols-2 xl:grid-cols-3">
        {PRESETS.map((p) => {
          const style = STYLE_MAP[p.style]
          return (
            <article
              key={p.id}
              className="card group relative flex flex-col gap-2 p-3.5 transition-all hover:border-brand-500/40 hover:bg-white/[0.06]"
            >
              <div className="flex items-start gap-2.5">
                <span className="text-xl leading-none">{p.emoji}</span>
                <div className="min-w-0 flex-1">
                  <h3 className="text-[13px] font-semibold leading-snug text-zinc-100">{p.title}</h3>
                  <div className="mt-1.5 flex flex-wrap items-center gap-1">
                    <span className="chip !text-[10px]">{p.tag}</span>
                    <span className="chip !text-[10px]">
                      {style.emoji} {style.short}
                    </span>
                    <span className="chip !text-[10px]">{p.aspect}</span>
                  </div>
                </div>
              </div>

              <p className="line-clamp-2 text-[11.5px] leading-relaxed text-zinc-500">{p.prompt}</p>

              <div className="mt-auto flex gap-1.5 pt-1">
                <button onClick={() => onUse(p)} className="btn-primary btn-sm flex-1">
                  <IconSparkles width={13} height={13} />
                  Use preset
                </button>
                <button
                  onClick={() => handleCopy(p)}
                  className="btn-ghost btn-sm"
                  aria-label={`Copy prompt for ${p.title}`}
                  title="Copy prompt"
                >
                  {copied === p.id ? (
                    <IconCheck width={13} height={13} className="text-emerald-400" />
                  ) : (
                    <IconCopy width={13} height={13} />
                  )}
                </button>
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}
