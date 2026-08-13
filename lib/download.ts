import { ASPECT_MAP, type AspectId } from './styles'

export function slugify(text: string, max = 48): string {
  return (
    text
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, max) || 'generation'
  )
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 4000)
}

/**
 * Upscale an image to true 4K on the client (progressive high-quality canvas
 * resample), so the PNG export matches the promised 4K resolution.
 */
export async function upscaleToBlob(
  src: Blob | string,
  aspect: AspectId,
  mime: 'image/png' | 'image/jpeg' = 'image/png',
): Promise<Blob> {
  const url = typeof src === 'string' ? src : URL.createObjectURL(src)
  try {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const i = new Image()
      i.crossOrigin = 'anonymous'
      i.onload = () => resolve(i)
      i.onerror = () => reject(new Error('Could not read image for export'))
      i.src = url
    })

    const { width: W, height: H } = ASPECT_MAP[aspect]

    // Progressive 2x steps preserve detail far better than one big jump.
    let cur = document.createElement('canvas')
    cur.width = img.naturalWidth
    cur.height = img.naturalHeight
    let cx = cur.getContext('2d')!
    cx.drawImage(img, 0, 0)

    while (cur.width * 2 <= W) {
      const next = document.createElement('canvas')
      next.width = cur.width * 2
      next.height = cur.height * 2
      const nx = next.getContext('2d')!
      nx.imageSmoothingEnabled = true
      nx.imageSmoothingQuality = 'high'
      nx.drawImage(cur, 0, 0, next.width, next.height)
      cur = next
      cx = nx
    }

    const out = document.createElement('canvas')
    out.width = W
    out.height = H
    const ox = out.getContext('2d')!
    ox.imageSmoothingEnabled = true
    ox.imageSmoothingQuality = 'high'

    // Cover-fit so we never letterbox the export.
    const s = Math.max(W / cur.width, H / cur.height)
    const dw = cur.width * s
    const dh = cur.height * s
    ox.drawImage(cur, (W - dw) / 2, (H - dh) / 2, dw, dh)

    const blob = await new Promise<Blob | null>((resolve) =>
      out.toBlob(resolve, mime, mime === 'image/jpeg' ? 0.95 : undefined),
    )
    if (!blob) throw new Error('Export failed')
    return blob
  } finally {
    if (typeof src !== 'string') setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
}

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    try {
      const ta = document.createElement('textarea')
      ta.value = text
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      const ok = document.execCommand('copy')
      ta.remove()
      return ok
    } catch {
      return false
    }
  }
}
