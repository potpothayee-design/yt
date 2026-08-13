# 📦 Tiny Workers Studio

A free, keyless AI generator for **Tiny Workers / Cardboard Puzzle / Pixar** style
images and videos. No credits, no watermark, no login, no paid API.

Built with **Next.js 14 · React 18 · TypeScript · Tailwind CSS**. Everything runs
in the browser — there is no backend.

---

## Features

| | |
|---|---|
| 🖼️ **Text to Image** | Prompt → image in 3 locked-in styles (Photoreal, Pixar 3D, Kraft Cardboard), 9:16 / 16:9 / 1:1, batch up to 4. |
| 🎬 **Image to Video** | Two engines: real AI diffusion motion (Wan / LTX / SVD on free community GPUs) or instant cinematic camera motion rendered on-device. |
| ⚡ **7 Viral Presets** | One tap loads a full prompt + style + aspect ratio. |
| 🗂️ **Gallery** | Saved on your device (IndexedDB), survives refresh. Download MP4 / 4K PNG, copy any prompt. |
| 🌑 **Dark UI** | Mobile responsive, Seedance-style dark interface. |

---

## Run locally

Requires [Node.js](https://nodejs.org) 18.17+ (LTS recommended).

```bash
npm install
npm run dev
```

Open <http://localhost:3000>. The dev server binds `0.0.0.0`, so it also works
from another device on your network.

**No `.env` needed.** Copy `.env.example` → `.env` only if you want the optional
Hugging Face token; the app is fully functional without one.

### Production

```bash
npm run build
npm start
```

Deploy anywhere that runs Node (Vercel, Netlify, Railway, your own VPS). Zero
configuration and no environment variables are required.

---

## How it works (and stays free)

**Images — [Pollinations](https://pollinations.ai) (Flux).** Free, keyless,
unlimited, called **directly from the browser**, so there is no server to
rate-limit and no key to leak. If one model is busy the app retries across
`flux → turbo → flux-realism` with a fresh seed.

**4K export.** Pollinations gets slow above ~1.5K per side, so the app renders at
a fast master size and progressively upscales to true 4K (2160×3840 / 3840×2160)
on a canvas at download time.

**Video — two engines, pick per render:**

1. **Real AI motion** — image-to-video diffusion (Wan 2.1 / LTX / SVD) on free
   community Hugging Face Spaces. No account, no card. The cost is a queue:
   shared GPUs mean 1–8 minutes, and Spaces sometimes sleep or hit daily quota.
   The app tries three Spaces in order before giving up.
2. **Cinematic camera** — animates your frames on a `<canvas>` with eased
   dolly/pan/crane/orbit/handheld moves, crossfades, grain and vignette, recorded
   to H.264 MP4 via `MediaRecorder`. Renders in seconds, works offline, never fails.

If the AI engines are all busy the app automatically falls back to camera motion,
so you always walk away with a clip.

> Nothing you make is ever uploaded to a server of ours — there is no backend at all.

---

## Network note

Images and AI-motion video call **third-party services from your browser**:

- `image.pollinations.ai` (images)
- `*.hf.space` (AI-motion video)

These need to be reachable from wherever the browser runs. If you are behind a
restricted network or a sandbox that only allows certain domains (GitHub, npm,
etc.), image generation and AI motion will fail there — but the **cinematic
camera** renderer, uploads, presets and gallery still work, because they are
100% local. Run on your own machine or a normal host and everything works.

---

## Project structure

```
app/
  layout.tsx        Metadata, fonts, ambient background
  page.tsx          Tab routing + shared state
  globals.css       Tailwind layers, dark theme, component classes
components/
  Header.tsx        Sticky nav with tab switcher
  TextToImage.tsx   Prompt, style, aspect, batch, 4K export
  ImageToVideo.tsx  Upload/generate frames, camera moves, render
  Gallery.tsx       Grid, filters, lightbox, downloads
  PresetGrid.tsx    The 7 viral presets
  Toast.tsx         Notification system
  Icons.tsx         Inline SVG icon set
lib/
  pollinations.ts   Free image engine + multi-model retry
  aivideo.ts        Real AI motion via free Hugging Face Spaces (Wan/LTX/SVD)
  video.ts          Canvas cinema renderer + MediaRecorder encoding
  storage.ts        IndexedDB gallery persistence
  download.ts       4K upscaling, blob download, clipboard
  presets.ts        The 7 prompts
  styles.ts         Style suffixes, negatives, aspect ratios
  types.ts          Shared types
```

---

## Troubleshooting

- **Video downloads as `.webm` instead of `.mp4`** — your browser lacks H.264
  canvas recording (mostly Firefox). Chrome, Edge and Safari produce MP4. WebM
  uploads fine to YouTube, TikTok and Instagram anyway.
- **First image is slow** — Pollinations cold-starts at 15–40s. Later renders are
  much faster.
- **AI motion says "engines busy"** — free community GPUs are shared and genuinely
  run out. Retry in a few minutes, or use the Cinematic camera engine for an
  instant result.
- **Keep the tab visible while rendering video** — browsers throttle background
  tabs, which slows capture.
- **Dev server 500s after `npm run build`** — the production build overwrites the
  `.next` folder the dev server watches. Fix: `rm -rf .next && npm run dev`.

## License

MIT — do whatever you want with it, including commercial use.
