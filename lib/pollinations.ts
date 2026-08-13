import { STYLE_MAP, type AspectId, type StyleId } from './styles'

/**
 * Pollinations is a free, keyless, unlimited image endpoint.
 * We call it straight from the browser, so there is no backend to rate-limit
 * and no API key to leak.
 */
const POLLINATIONS = 'https://image.pollinations.ai/prompt/'

/** Models we round-robin through if one is busy. */
export const IMAGE_MODELS = ['flux', 'turbo', 'flux-realism'] as const
export type ImageModel = (typeof IMAGE_MODELS)[number]

export function buildPrompt(prompt: string, style: StyleId | null, extra?: string): string {
  const parts = [prompt.trim()]
  if (style && STYLE_MAP[style]) parts.push(STYLE_MAP[style].suffix)
  if (extra?.trim()) parts.push(extra.trim())
  parts.push('no text, no watermark, no logo, no signature')
  return parts.filter(Boolean).join(', ')
}

function negativeFor(style: StyleId | null): string {
  return style && STYLE_MAP[style]
    ? STYLE_MAP[style].negative
    : 'text, watermark, logo, lowres, blurry, deformed'
}

/** Master render size — Pollinations gets slow above ~1.5K a side; we upscale to 4K on export. */
function renderSizeFor(aspect: AspectId): { width: number; height: number } {
  switch (aspect) {
    case '9:16':
      return { width: 864, height: 1536 }
    case '16:9':
      return { width: 1536, height: 864 }
    default:
      return { width: 1216, height: 1216 }
  }
}

export interface ImageUrlArgs {
  prompt: string
  style: StyleId | null
  aspect: AspectId
  seed: number
  model?: ImageModel
  extra?: string
}

export interface ImageUrl {
  url: string
  finalPrompt: string
  width: number
  height: number
}

export function buildImageUrl({
  prompt,
  style,
  aspect,
  seed,
  model = 'flux',
  extra,
}: ImageUrlArgs): ImageUrl {
  const finalPrompt = buildPrompt(prompt, style, extra)
  const { width, height } = renderSizeFor(aspect)
  const qs = new URLSearchParams({
    width: String(width),
    height: String(height),
    seed: String(seed),
    model,
    nologo: 'true',
    enhance: 'true',
    private: 'true',
    negative: negativeFor(style),
  })
  return { url: `${POLLINATIONS}${encodeURIComponent(finalPrompt)}?${qs.toString()}`, finalPrompt, width, height }
}

export function randomSeed(): number {
  return Math.floor(Math.random() * 1_000_000_000)
}

/**
 * Strategy A — fetch() into a Blob. Requires permissive CORS (Pollinations sends it).
 * Gives a real Blob we can persist and canvas-export without tainting.
 */
async function viaFetch(url: string, timeoutMs: number): Promise<Blob> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(url, { signal: controller.signal, mode: 'cors' })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const blob = await res.blob()
    if (blob.size < 1024) throw new Error('Empty image returned')
    return blob
  } finally {
    clearTimeout(timer)
  }
}

/**
 * Strategy B — <img crossOrigin="anonymous"> then canvas.toBlob(). <img> loading is
 * not subject to the same fetch CORS rules, so this works where fetch() is rejected.
 */
function viaImageCanvas(url: string, timeoutMs: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    const timer = setTimeout(() => {
      img.src = ''
      reject(new Error('Image load timed out'))
    }, timeoutMs)

    img.onload = () => {
      clearTimeout(timer)
      try {
        const c = document.createElement('canvas')
        c.width = img.naturalWidth
        c.height = img.naturalHeight
        const cx = c.getContext('2d')
        if (!cx) throw new Error('No canvas context')
        cx.drawImage(img, 0, 0)
        // Throws a SecurityError if the canvas was tainted.
        c.toBlob(
          (b) => (b && b.size > 1024 ? resolve(b) : reject(new Error('Canvas export failed'))),
          'image/jpeg',
          0.95,
        )
      } catch (e) {
        reject(e)
      }
    }
    img.onerror = () => {
      clearTimeout(timer)
      reject(new Error('Image failed to load'))
    }
    img.src = url
  })
}

export interface ImageResult {
  blob: Blob
  finalPrompt: string
  width: number
  height: number
  model: string
  seed: number
  /** Set when we could only obtain a remote URL, not real pixel data. */
  remoteUrl?: string
}

/**
 * Fetch an image, trying every model and every transport before giving up.
 * Only if both transports fail for all models do we fall back to the raw URL,
 * so the user still sees their picture even in a hostile CORS environment.
 */
export async function fetchImageBlob(
  args: ImageUrlArgs,
  opts: { timeoutMs?: number; onAttempt?: (model: string, attempt: number) => void } = {},
): Promise<ImageResult> {
  const { timeoutMs = 105_000, onAttempt } = opts
  const models: ImageModel[] = args.model
    ? [args.model, ...IMAGE_MODELS.filter((m) => m !== args.model)]
    : [...IMAGE_MODELS]

  let lastErr: unknown
  let lastUrl = ''
  let lastMeta = { finalPrompt: '', width: 0, height: 0, seed: args.seed }

  for (let i = 0; i < models.length; i++) {
    const model = models[i]
    // A fresh seed on retry avoids a poisoned cache entry.
    const seed = i === 0 ? args.seed : randomSeed()
    onAttempt?.(model, i + 1)
    const { url, finalPrompt, width, height } = buildImageUrl({ ...args, model, seed })
    lastUrl = url
    lastMeta = { finalPrompt, width, height, seed }

    for (const transport of [viaFetch, viaImageCanvas]) {
      try {
        const blob = await transport(url, timeoutMs)
        return { blob, finalPrompt, width, height, model, seed }
      } catch (err) {
        lastErr = err
      }
    }
  }

  // Last resort: confirm the URL renders as an <img> at all. If it does, show it.
  try {
    await new Promise<void>((resolve, reject) => {
      const img = new Image()
      const timer = setTimeout(() => reject(new Error('timeout')), timeoutMs)
      img.onload = () => {
        clearTimeout(timer)
        resolve()
      }
      img.onerror = () => {
        clearTimeout(timer)
        reject(new Error('failed'))
      }
      img.src = lastUrl
    })
    return { blob: new Blob(), ...lastMeta, model: 'direct', remoteUrl: lastUrl }
  } catch {
    /* fall through to the thrown error below */
  }

  throw new Error(
    `Image engines are not responding${
      lastErr instanceof Error ? ` (${lastErr.message})` : ''
    }. Check your connection and try again — nothing was charged, you have unlimited retries.`,
  )
}
