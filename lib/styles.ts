export type StyleId = 'photoreal' | 'pixar' | 'kraft'

export interface StylePreset {
  id: StyleId
  name: string
  short: string
  emoji: string
  /** Appended to the user prompt to lock the look. */
  suffix: string
  /** Things we never want to see. */
  negative: string
  swatch: string
}

export const STYLES: StylePreset[] = [
  {
    id: 'photoreal',
    name: 'Photorealistic Tiny Workers',
    short: 'Photoreal',
    emoji: '🔧',
    suffix:
      'hyper photorealistic macro photography, tiny miniature workers in realistic hi-vis safety gear and hard hats, ' +
      'scale 1:64 diorama realism, shallow depth of field, 100mm macro lens, f/2.8, cinematic volumetric lighting, ' +
      'soft golden rim light, dust particles floating in the air, ultra detailed fabric and skin texture, ' +
      'sharp focus, physically based rendering, 8k UHD, shot on Sony A7R IV, tilt-shift miniature realism',
    negative:
      'cartoon, anime, illustration, painting, lowres, blurry, deformed hands, extra limbs, text, watermark, logo, jpeg artifacts, oversaturated',
    swatch: 'from-amber-500/80 to-orange-700/80',
  },
  {
    id: 'pixar',
    name: 'Pixar 3D Cartoon',
    short: 'Pixar 3D',
    emoji: '🎬',
    suffix:
      'Pixar Disney 3D animated movie style, adorable stylized characters with big expressive eyes, ' +
      'subsurface scattering skin, soft global illumination, warm cinematic three point lighting, ' +
      'glossy toy-like materials, rounded friendly shapes, emotional storytelling frame, ' +
      'rendered in Octane and RenderMan, ultra detailed, 3D animation still, 8k',
    negative:
      'photorealistic human, horror, gore, scary, text, watermark, logo, lowres, blurry, deformed, extra fingers, ugly',
    swatch: 'from-sky-400/80 to-indigo-600/80',
  },
  {
    id: 'kraft',
    name: 'Kraft Cardboard Puzzle',
    short: 'Cardboard',
    emoji: '📦',
    suffix:
      'made entirely of brown kraft corrugated cardboard, laser cut jigsaw puzzle pieces slotting together, ' +
      'visible corrugation fluting on every cut edge, papercraft diorama, handcrafted DIY model kit aesthetic, ' +
      'warm studio softbox lighting on a clean paper backdrop, tactile recycled paper texture, ' +
      'cardboard tabs and slots, macro product photography, ultra detailed, 8k',
    negative:
      'plastic, metal, glass, glossy chrome, neon, text, watermark, logo, lowres, blurry, messy, cluttered background',
    swatch: 'from-amber-700/80 to-yellow-900/80',
  },
]

export const STYLE_MAP: Record<StyleId, StylePreset> = STYLES.reduce(
  (acc, s) => ({ ...acc, [s.id]: s }),
  {} as Record<StyleId, StylePreset>,
)

export type AspectId = '9:16' | '16:9' | '1:1'

export interface AspectPreset {
  id: AspectId
  label: string
  hint: string
  /** 4K-class render size (kept within model-friendly bounds, upscaled on export). */
  width: number
  height: number
  /** Tailwind ratio class for previews. */
  ratioClass: string
}

export const ASPECTS: AspectPreset[] = [
  {
    id: '9:16',
    label: '9:16',
    hint: 'Shorts / Reels / TikTok',
    width: 2160,
    height: 3840,
    ratioClass: 'aspect-[9/16]',
  },
  {
    id: '16:9',
    label: '16:9',
    hint: 'YouTube / Desktop',
    width: 3840,
    height: 2160,
    ratioClass: 'aspect-video',
  },
  {
    id: '1:1',
    label: '1:1',
    hint: 'Thumbnail / Post',
    width: 2880,
    height: 2880,
    ratioClass: 'aspect-square',
  },
]

export const ASPECT_MAP: Record<AspectId, AspectPreset> = ASPECTS.reduce(
  (acc, a) => ({ ...acc, [a.id]: a }),
  {} as Record<AspectId, AspectPreset>,
)
