import type { AspectId, StyleId } from './styles'

export type AssetKind = 'image' | 'video'

export interface GalleryItem {
  id: string
  kind: AssetKind
  /** Object URL or remote URL for display. */
  url: string
  /** Stored blob (IndexedDB) so downloads never re-hit the network. */
  mime: string
  prompt: string
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
