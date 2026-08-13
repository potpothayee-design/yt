import type { AspectId, StyleId } from './styles'

export type AssetKind = 'image' | 'video'

export interface GalleryItem {
  id: string
  kind: AssetKind
  /** Object URL or remote URL used for display. */
  url: string
  mime: string
  /** Fully expanded prompt (with style suffix). */
  prompt: string
  /** What the user actually typed. */
  rawPrompt: string
  style: StyleId | null
  aspect: AspectId
  engine: string
  seed?: number
  width: number
  height: number
  durationSec?: number
  createdAt: number
}
