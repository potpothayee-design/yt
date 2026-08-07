import { ASPECT_MAP, type AspectId } from './styles'

/**
 * Client-side cinematic video engine.
 *
 * Why client-side? Free hosted video models (Wan2.1, SVD, ...) are gated,
 * queued or cold-booting most of the time, so relying on them alone means the
 * app breaks exactly like the paid tools do. Instead we always have a guaranteed
 * renderer: we animate real camera moves over one or more AI keyframes on a
 * <canvas> and capture it with MediaRecorder into a real, downloadable video
 * file. No key, no queue, no credits, no watermark — it simply never fails.
 */

export type MotionId =
  | 'push-in'
  | 'pull-out'
  | 'pan-right'
  | 'pan-left'
  | 'crane-up'
  | 'orbit'
  | 'handheld'
  | 'split-wipe'

export interface MotionPreset {
  id: MotionId
  label: string
  hint: string
}

export const MOTIONS: MotionPreset[] = [
  { id: 'push-in', label: 'Push in', hint: 'Slow cinematic dolly toward the subject' },
  { id: 'pull-out', label: 'Pull out', hint: 'Reveal the whole scene' },
  { id: 'pan-right', label: 'Pan right', hint: 'Lateral tracking move' },
  { id: 'pan-left', label: 'Pan left', hint: 'Lateral tracking move' },
  { id: 'crane-up', label: 'Crane up', hint: 'Rise over the diorama' },
  { id: 'orbit', label: 'Orbit', hint: 'Subtle parallax arc' },
  { id: 'handheld', label: 'Handheld', hint: 'Organic documentary sway' },
  { id: 'split-wipe', label: 'Split wipe', hint: 'Before / after sweep — great for restorations' },
]

export interface RenderOptions {
  images: HTMLImageElement[]
  aspect: AspectId
  durationSec: number
  motion: MotionId
  fps?: number
  grain?: boolean
  vignette?: boolean
  onProgress?: (pct: number) => void
  signal?: AbortSignal
}

export interface RenderResult {
  blob: Blob
  mime: string
  ext: 'mp4' | 'webm'
  width: number
  height: number
  durationSec: number
}

/** Output resolution — 1080x1920 / 1920x1080 keeps encoding realtime-fast. */
function outputSize(aspect: AspectId) {
  switch (aspect) {
    case '9:16':
      return { width: 1080, height: 1920 }
    case '16:9':
      return { width: 1920, height: 1080 }
    default:
      return { width: 1440, height: 1440 }
  }
}

function pickMime(): { mime: string; ext: 'mp4' | 'webm' } {
  const candidates: { mime: string; ext: 'mp4' | 'webm' }[] = [
    { mime: 'video/mp4;codecs=avc1.42E01E', ext: 'mp4' },
    { mime: 'video/mp4;codecs=h264', ext: 'mp4' },
    { mime: 'video/mp4', ext: 'mp4' },
    { mime: 'video/webm;codecs=vp9', ext: 'webm' },
    { mime: 'video/webm;codecs=vp8', ext: 'webm' },
    { mime: 'video/webm', ext: 'webm' },
  ]
  for (const c of candidates) {
    if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(c.mime)) return c
  }
  return { mime: '', ext: 'webm' }
}

export function supportsRecording(): boolean {
  return (
    typeof MediaRecorder !== 'undefined' &&
    typeof HTMLCanvasElement !== 'undefined' &&
    typeof HTMLCanvasElement.prototype.captureStream === 'function'
  )
}

/** easeInOutCubic — gives moves that accelerate and settle like a real dolly. */
function ease(t: number): number {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
}

interface CamState {
  scale: number
  tx: number
  ty: number
  rot: number
}

function cameraAt(motion: MotionId, p: number): CamState {
  const e = ease(p)
  switch (motion) {
    case 'push-in':
      return { scale: 1.04 + e * 0.22, tx: 0, ty: -e * 0.012, rot: 0 }
    case 'pull-out':
      return { scale: 1.3 - e * 0.24, tx: 0, ty: e * 0.01, rot: 0 }
    case 'pan-right':
      return { scale: 1.16, tx: -0.06 + e * 0.12, ty: 0, rot: 0 }
    case 'pan-left':
      return { scale: 1.16, tx: 0.06 - e * 0.12, ty: 0, rot: 0 }
    case 'crane-up':
      return { scale: 1.14 + e * 0.06, tx: 0, ty: 0.07 - e * 0.14, rot: 0 }
    case 'orbit':
      return {
        scale: 1.18,
        tx: Math.sin(p * Math.PI * 2) * 0.045,
        ty: Math.cos(p * Math.PI * 2) * 0.02 - 0.02,
        rot: Math.sin(p * Math.PI * 2) * 0.012,
      }
    case 'handheld': {
      const t = p * Math.PI * 2
      return {
        scale: 1.1 + e * 0.06,
        tx: (Math.sin(t * 1.7) + Math.sin(t * 3.1) * 0.5) * 0.008,
        ty: (Math.cos(t * 1.3) + Math.cos(t * 2.7) * 0.5) * 0.008,
        rot: Math.sin(t * 0.9) * 0.006,
      }
    }
    case 'split-wipe':
      return { scale: 1.08 + e * 0.05, tx: 0, ty: 0, rot: 0 }
    default:
      return { scale: 1.1, tx: 0, ty: 0, rot: 0 }
  }
}

/** Draw an image "cover" style into WxH with a camera transform applied. */
function drawFrame(
  ctx: CanvasRenderingContext2D,
  img: HTMLImageElement,
  W: number,
  H: number,
  cam: CamState,
  alpha: number,
) {
  const iw = img.naturalWidth || img.width
  const ih = img.naturalHeight || img.height
  if (!iw || !ih) return
  const coverScale = Math.max(W / iw, H / ih)
  const dw = iw * coverScale * cam.scale
  const dh = ih * coverScale * cam.scale

  ctx.save()
  ctx.globalAlpha = alpha
  ctx.translate(W / 2 + cam.tx * W, H / 2 + cam.ty * H)
  if (cam.rot) ctx.rotate(cam.rot)
  ctx.drawImage(img, -dw / 2, -dh / 2, dw, dh)
  ctx.restore()
}

function drawVignette(ctx: CanvasRenderingContext2D, W: number, H: number) {
  const g = ctx.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.32, W / 2, H / 2, Math.max(W, H) * 0.75)
  g.addColorStop(0, 'rgba(0,0,0,0)')
  g.addColorStop(1, 'rgba(0,0,0,0.42)')
  ctx.save()
  ctx.fillStyle = g
  ctx.fillRect(0, 0, W, H)
  ctx.restore()
}

function makeGrainTile(size = 128): HTMLCanvasElement {
  const c = document.createElement('canvas')
  c.width = c.height = size
  const cx = c.getContext('2d')!
  const data = cx.createImageData(size, size)
  for (let i = 0; i < data.data.length; i += 4) {
    const v = 110 + Math.random() * 90
    data.data[i] = data.data[i + 1] = data.data[i + 2] = v
    data.data[i + 3] = 255
  }
  cx.putImageData(data, 0, 0)
  return c
}

export async function renderVideo(opts: RenderOptions): Promise<RenderResult> {
  const {
    images,
    aspect,
    durationSec,
    motion,
    fps = 30,
    grain = true,
    vignette = true,
    onProgress,
    signal,
  } = opts

  if (!images.length) throw new Error('No source image to animate.')
  if (!supportsRecording()) {
    throw new Error(
      'Your browser cannot record canvas video. Try Chrome, Edge or Safari on desktop, or download the still image instead.',
    )
  }

  const { width: W, height: H } = outputSize(aspect)
  const canvas = document.createElement('canvas')
  canvas.width = W
  canvas.height = H
  const ctx = canvas.getContext('2d', { alpha: false })!
  ctx.imageSmoothingEnabled = true
  ctx.imageSmoothingQuality = 'high'

  const { mime, ext } = pickMime()
  const stream = canvas.captureStream(fps)
  const recorder = new MediaRecorder(stream, {
    ...(mime ? { mimeType: mime } : {}),
    videoBitsPerSecond: 12_000_000,
  })

  const chunks: BlobPart[] = []
  recorder.ondataavailable = (e) => {
    if (e.data && e.data.size) chunks.push(e.data)
  }

  const stopped = new Promise<void>((resolve) => {
    recorder.onstop = () => resolve()
  })

  const grainTile = grain ? makeGrainTile() : null
  const grainPattern = grainTile ? ctx.createPattern(grainTile, 'repeat') : null

  const totalFrames = Math.max(1, Math.round(durationSec * fps))
  // Keyframe crossfade: distribute all source images across the timeline.
  const segs = Math.max(1, images.length - 1)

  recorder.start()
  const frameMs = 1000 / fps
  let start = performance.now()

  for (let f = 0; f < totalFrames; f++) {
    if (signal?.aborted) {
      recorder.stop()
      await stopped
      throw new DOMException('Render cancelled', 'AbortError')
    }
    const p = totalFrames === 1 ? 0 : f / (totalFrames - 1)
    const cam = cameraAt(motion, p)

    ctx.fillStyle = '#000'
    ctx.fillRect(0, 0, W, H)

    if (images.length === 1) {
      drawFrame(ctx, images[0], W, H, cam, 1)
    } else {
      const pos = p * segs
      const idx = Math.min(images.length - 2, Math.floor(pos))
      const local = pos - idx
      // Hold each keyframe, then crossfade over the last 35% of its segment.
      const fade = local < 0.65 ? 0 : (local - 0.65) / 0.35
      drawFrame(ctx, images[idx], W, H, cam, 1)
      if (fade > 0) drawFrame(ctx, images[idx + 1], W, H, cam, ease(fade))
    }

    if (motion === 'split-wipe') {
      const x = Math.round(ease(p) * W)
      ctx.save()
      // Cool grade on the "before" side, warm on the "after" side.
      ctx.globalCompositeOperation = 'multiply'
      ctx.fillStyle = 'rgba(150,190,255,0.55)'
      ctx.fillRect(0, 0, x, H)
      ctx.fillStyle = 'rgba(255,205,150,0.4)'
      ctx.fillRect(x, 0, W - x, H)
      ctx.restore()
      ctx.save()
      ctx.fillStyle = 'rgba(255,255,255,0.95)'
      ctx.fillRect(x - 2, 0, 4, H)
      ctx.shadowColor = 'rgba(255,255,255,0.9)'
      ctx.shadowBlur = 28
      ctx.fillRect(x - 1, 0, 2, H)
      ctx.restore()
    }

    if (vignette) drawVignette(ctx, W, H)

    if (grainPattern) {
      ctx.save()
      ctx.globalAlpha = 0.045
      ctx.globalCompositeOperation = 'overlay'
      ctx.translate(Math.random() * 128, Math.random() * 128)
      ctx.fillStyle = grainPattern
      ctx.fillRect(-128, -128, W + 256, H + 256)
      ctx.restore()
    }

    // Fade from / to black so clips loop and cut cleanly.
    const fadeIn = Math.min(1, p / 0.06)
    const fadeOut = Math.min(1, (1 - p) / 0.06)
    const dark = 1 - Math.min(fadeIn, fadeOut)
    if (dark > 0.001) {
      ctx.save()
      ctx.fillStyle = `rgba(0,0,0,${dark})`
      ctx.fillRect(0, 0, W, H)
      ctx.restore()
    }

    onProgress?.(Math.round((f / totalFrames) * 100))

    // Pace the loop to real time so the recorder timestamps stay correct.
    const target = start + (f + 1) * frameMs
    const wait = target - performance.now()
    await new Promise((r) => setTimeout(r, wait > 0 ? wait : 0))
  }

  recorder.stop()
  await stopped
  onProgress?.(100)

  const blob = new Blob(chunks, { type: mime || 'video/webm' })
  return { blob, mime: mime || 'video/webm', ext, width: W, height: H, durationSec }
}

export function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('Could not load image'))
    img.src = src
  })
}
