import type { AspectId } from './styles'

/**
 * TRUE AI MOTION ENGINE (free, no credits, no card).
 *
 * Runs open-source image-to-video diffusion models (Wan / LTX / SVD) on free
 * community Hugging Face Spaces via the Gradio client. Real diffusion motion —
 * objects, characters and materials actually move.
 *
 * Honest trade-offs (surfaced in the UI): shared community GPUs mean a queue
 * (often 1–8 min); Spaces sleep, restart, hit daily quota, or get deleted.
 * Because any single Space is unreliable we try a chain of them in order and
 * fall back to the local canvas renderer if they all fail.
 */

export interface SpaceTarget {
  /** Hugging Face Space id. */
  id: string
  label: string
  model: string
  /** Named gradio endpoint to call. */
  api: string
  /** Builds the payload for this Space's signature. */
  build: (args: {
    image: Blob
    prompt: string
    durationSec: number
    aspect: AspectId
  }) => unknown[] | Record<string, unknown>
  notes?: string
}

/** Ordered by speed x reliability. Signatures differ per Space, so each builds its own payload. */
export const SPACES: SpaceTarget[] = [
  {
    id: 'Lightricks/ltx-video-distilled',
    label: 'LTX Video (distilled)',
    model: 'LTX-Video',
    api: '/image_to_video',
    notes: 'Fastest free option — usually the shortest queue.',
    build: ({ image, prompt, durationSec }) => ({
      image,
      prompt,
      negative_prompt: 'worst quality, blurry, jittery, distorted, watermark, text',
      duration: Math.min(durationSec, 5),
      randomize_seed: true,
      improve_texture: true,
    }),
  },
  {
    id: 'multimodalart/wan2-1-fast',
    label: 'Wan 2.1 (fast)',
    model: 'Wan2.1-I2V',
    api: '/generate_video',
    notes: 'Best motion quality of the free set.',
    build: ({ image, prompt, durationSec }) => ({
      input_image: image,
      prompt,
      negative_prompt: 'worst quality, blurry, distorted, watermark, text',
      duration_seconds: Math.min(durationSec, 5),
      steps: 4,
      randomize_seed: true,
    }),
  },
  {
    id: 'multimodalart/stable-video-diffusion',
    label: 'Stable Video Diffusion',
    model: 'SVD-XT',
    api: '/video',
    notes: 'Camera-led motion, no text prompt.',
    build: ({ image }) => [image, 0, true, 127, 6],
  },
]

export interface AiVideoResult {
  blob: Blob
  mime: string
  ext: string
  space: string
  model: string
}

export interface AiVideoOptions {
  image: Blob
  prompt: string
  durationSec: number
  aspect: AspectId
  /** Optional HF token — raises quota, but everything works without one. */
  token?: string
  onStatus?: (msg: string) => void
  signal?: AbortSignal
}

/** Pull a usable video URL out of whatever shape a Space returns. */
function extractVideoUrl(data: unknown): string | null {
  const seen = new Set<unknown>()
  const walk = (node: unknown, depth = 0): string | null => {
    if (node == null || depth > 6 || seen.has(node)) return null
    if (typeof node === 'object') seen.add(node)

    if (typeof node === 'string') {
      return /^https?:\/\/.+\.(mp4|webm|gif)(\?|$)/i.test(node) ? node : null
    }
    if (Array.isArray(node)) {
      for (const v of node) {
        const hit = walk(v, depth + 1)
        if (hit) return hit
      }
      return null
    }
    if (typeof node === 'object') {
      const o = node as Record<string, unknown>
      for (const key of ['url', 'video', 'path', 'data', 'value']) {
        if (key in o) {
          const hit = walk(o[key], depth + 1)
          if (hit) return hit
        }
      }
      for (const v of Object.values(o)) {
        const hit = walk(v, depth + 1)
        if (hit) return hit
      }
    }
    return null
  }
  return walk(data)
}

/** Try one Space. Resolves with a video Blob or throws. */
async function trySpace(target: SpaceTarget, opts: AiVideoOptions): Promise<AiVideoResult> {
  const { image, prompt, durationSec, aspect, token, onStatus } = opts

  onStatus?.(`Connecting to ${target.label}…`)

  // Imported lazily so the ~100KB client never lands in the initial bundle.
  const { Client } = await import('@gradio/client')
  const client = await Client.connect(target.id, {
    ...(token ? { hf_token: token as `hf_${string}` } : {}),
  })

  onStatus?.(`Queued on ${target.label} — free community GPU, this can take a few minutes…`)

  const payload = target.build({ image, prompt, durationSec, aspect })
  const result = await client.predict(target.api, payload as never)

  const url = extractVideoUrl((result as { data?: unknown })?.data ?? result)
  if (!url) throw new Error(`${target.label} returned no video`)

  onStatus?.(`Downloading result from ${target.label}…`)
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Could not download from ${target.label} (HTTP ${res.status})`)
  const blob = await res.blob()
  if (blob.size < 2048) throw new Error(`${target.label} returned an empty file`)

  const ext = url.match(/\.(mp4|webm|gif)/i)?.[1]?.toLowerCase() ?? 'mp4'
  return { blob, mime: blob.type || `video/${ext}`, ext, space: target.id, model: target.model }
}

/** Generate real AI motion, walking the Space chain until one succeeds. */
export async function generateAiVideo(opts: AiVideoOptions): Promise<AiVideoResult> {
  const errors: string[] = []

  for (let i = 0; i < SPACES.length; i++) {
    const target = SPACES[i]
    if (opts.signal?.aborted) throw new DOMException('Cancelled', 'AbortError')

    opts.onStatus?.(`Engine ${i + 1}/${SPACES.length}: ${target.label}…`)
    try {
      return await trySpace(target, opts)
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      errors.push(`${target.label}: ${msg}`)
      opts.onStatus?.(`${target.label} unavailable — trying the next free engine…`)
    }
  }

  throw new Error(
    `All free AI motion engines are busy or offline right now. ` +
      `This is normal for free community GPUs. Details — ${errors.join(' | ')}`,
  )
}
