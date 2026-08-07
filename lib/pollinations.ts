import { ASPECT_MAP, STYLE_MAP, type AspectId, type StyleId } from './styles'

/**
 * Pollinations is a free, keyless, unlimited image endpoint.
 * We call it straight from the browser so there is no backend to rate limit,
 * no API key to leak, and the app still works as a pure static export.
 */
const POLLINATIONS = 'https://image.pollinations.ai/prompt/'

/** Models we can round-robin through if one is busy. */
export const IMAGE_MODELS = ['flux', 'turbo', 'flux-realism'] as const
export type ImageModel = (typeof IMAGE_MODELS)[number]

export interface BuildPromptArgs {
  prompt: string
  style: StyleId | null
  /** Extra words appended after the style suffix. */
  extra?: string
}

export function buildPrompt({ prompt, style, extra }: BuildPromptArgs): string {
  const parts = [prompt.trim()]
  if (style && STYLE_MAP[style]) parts.push(STYLE_MAP[style].suffix)
  if (extra?.trim()) parts.push(extra.trim())
  parts.push('no text, no watermark, no logo, no signature')
  return parts.filter(Boolean).join(', ')
}

export function negativeFor(style: StyleId | null): string {
  return style && STYLE_MAP[style]
    ? STYLE_MAP[style].negative
    : 'text, watermark, logo, lowres, blurry, deformed'
}

/**
 * Pollinations gets slow/unstable above ~1.5K on a side, so we render at a safe
 * "master" size and upscale to true 4K on the client during export.
 */
function renderSizeFor(aspect: AspectId) {
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

export function buildImageUrl({
  prompt,
  style,
  aspect,
  seed,
  model = 'flux',
  extra,
}: ImageUrlArgs): { url: string; finalPrompt: string; width: number; height: number } {
  const finalPrompt = buildPrompt({ prompt, style, extra })
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
  const url = `${POLLINATIONS}${encodeURIComponent(finalPrompt)}?${qs.toString()}`
  return { url, finalPrompt, width, height }
}

export function randomSeed(): number {
  return Math.floor(Math.random() * 1_000_000_000)
}

/** Load a URL into a Blob with a timeout + retry across models. */
export async function fetchImageBlob(
  args: ImageUrlArgs,
  opts: { timeoutMs?: number; onAttempt?: (model: string, attempt: number) => void } = {},
): Promise<{ blob: Blob; finalPrompt: string; width: number; height: number; model: string; seed: number }> {
  const { timeoutMs = 105_000, onAttempt } = opts
  const models: ImageModel[] = args.model
    ? [args.model, ...IMAGE_MODELS.filter((m) => m !== args.model)]
    : [...IMAGE_MODELS]

  let lastErr: unknown
  for (let i = 0; i < models.length; i++) {
    const model = models[i]
    // A fresh seed on retry avoids a poisoned cache entry.
    const seed = i === 0 ? args.seed : randomSeed()
    onAttempt?.(model, i + 1)
    const { url, finalPrompt, width, height } = buildImageUrl({ ...args, model, seed })
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeoutMs)
    try {
      const res = await fetch(url, { signal: controller.signal, mode: 'cors' })
      clearTimeout(timer)
      if (!res.ok) throw new Error(`Pollinations ${model} responded ${res.status}`)
      const blob = await res.blob()
      if (blob.size < 1024) throw new Error('Empty image returned')
      return { blob, finalPrompt, width, height, model, seed }
    } catch (err) {
      clearTimeout(timer)
      lastErr = err
    }
  }
  throw new Error(
    `All image engines failed. ${lastErr instanceof Error ? lastErr.message : ''} ` +
      `Check your internet connection and try again — no credits were used.`,
  )
}
