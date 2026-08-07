'use client'

import { createContext, useCallback, useContext, useMemo, useState } from 'react'

type ToastKind = 'success' | 'error' | 'info'

interface Toast {
  id: number
  kind: ToastKind
  message: string
}

const ToastCtx = createContext<(message: string, kind?: ToastKind) => void>(() => {})

export function useToast() {
  return useContext(ToastCtx)
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const push = useCallback((message: string, kind: ToastKind = 'info') => {
    const id = Date.now() + Math.random()
    setToasts((t) => [...t, { id, kind, message }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4200)
  }, [])

  const value = useMemo(() => push, [push])

  return (
    <ToastCtx.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 bottom-4 z-[100] flex flex-col items-center gap-2 px-4 sm:bottom-6">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`animate-fadeup pointer-events-auto flex max-w-md items-start gap-2.5 rounded-xl border px-4 py-3 text-sm shadow-2xl backdrop-blur-xl ${
              t.kind === 'success'
                ? 'border-emerald-500/30 bg-emerald-950/80 text-emerald-100'
                : t.kind === 'error'
                  ? 'border-red-500/30 bg-red-950/80 text-red-100'
                  : 'border-white/15 bg-ink-850/90 text-zinc-100'
            }`}
          >
            <span className="mt-0.5 shrink-0">
              {t.kind === 'success' ? '✓' : t.kind === 'error' ? '⚠' : 'ℹ'}
            </span>
            <span className="leading-snug">{t.message}</span>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  )
}
