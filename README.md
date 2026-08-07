# 📦 Tiny Workers Studio

**Free, unlimited AI generator for "Tiny Workers + Cardboard Puzzle + Pixar" images and videos.**
No credits. No watermark. No login. No paid API. It can't run out — because there's nothing to run out of.

Built with Next.js 14 · TypeScript · Tailwind CSS.

---

## ✨ Features

| | |
|---|---|
| 🖼️ **Text to Image** | Prompt → 4K image. 3 locked-in styles, 9:16 / 16:9 / 1:1, batch up to 4 at a time. |
| 🎬 **Image to Video** | Upload (or generate) frames → 5–8 second cinematic clip with real camera moves. |
| ⚡ **7 Viral Presets** | One tap loads the full prompt, style and aspect ratio. |
| 🗂️ **Gallery** | Saved on your device (IndexedDB), survives refresh. Download MP4 / 4K PNG, copy any prompt. |
| 🌑 **Dark UI** | Seedance-style interface, fully mobile responsive. |

### Styles
- **🔧 Photorealistic Tiny Workers** — macro realism, tilt-shift diorama, 100mm lens look
- **🎬 Pixar 3D Cartoon** — emotional animation still, subsurface scattering, warm key light
- **📦 Kraft Cardboard Puzzle** — corrugated papercraft, laser-cut jigsaw pieces, studio softbox

### The 7 presets
1. 🏎️ Tiny Workers Building Cardboard Ferrari
2. 🔩 Tiny Workers Disassembling Hot Wheels
3. 🥺 Pixar Sad Cardboard Car
4. ✨ Toy Story Cardboard Comes Alive
5. 🔊 ASMR Cardboard Engine
6. 🪄 Dual Restoration Split Screen
7. 🌃 3AM Tiny City

---

## 🚀 Run locally

```bash
npm install
npm run dev
```

Open <http://localhost:3000>. The dev server binds `0.0.0.0` so it also works from another device on your network.

**No `.env` needed.** Copy `.env.example` → `.env` only if you want to experiment with an optional Hugging Face token; the app is fully functional without one.

---

## 🧠 How it stays free forever

**Images — [Pollinations](https://pollinations.ai) (Flux).** Free, keyless, unlimited. Called **directly from your
browser**, so there's no backend to rate-limit, no API key to leak, and no server cost. If one model is busy the app
automatically retries across `flux → turbo → flux-realism` with a fresh seed.

**4K export.** Pollinations gets slow above ~1.5K per side, so we render at a fast master size and progressively
upscale to true 4K (2160×3840 / 3840×2160) on a canvas at download time. You get real 4K PNGs without the timeouts.

**Video — rendered locally in your browser.** Every free hosted video model (Wan2.1, SVD, …) is gated, queued or
cold-booting most of the time, which is exactly how the paid tools break. So instead the app animates your keyframes on
a `<canvas>` with real cinematography — eased dolly/pan/crane/orbit/handheld moves, multi-frame crossfades, film grain,
vignette, and fade in/out — and records it with `MediaRecorder` to a genuine MP4 (H.264, WebM fallback).

That means video generation has **zero queue, zero cold start, zero credits, and a 100% success rate.** It works
offline once the page is loaded.

> Nothing you make is ever uploaded to a server of ours — there is no backend at all.

---

## 📦 Deploy

### Vercel (recommended)
Import the repo and hit deploy. Zero configuration — no environment variables required.

```bash
npx vercel --prod
```

### GitHub Pages
Push to `main` and the included workflow (`.github/workflows/deploy.yml`) builds and publishes automatically.
Enable it once under **Settings → Pages → Source → GitHub Actions**.

To build a static bundle yourself:

```bash
BASE_PATH=/yt npm run build:static   # outputs ./out
```

`BASE_PATH` must match your repo name when serving from `https://<user>.github.io/<repo>/`.
Omit it for a custom domain or a `<user>.github.io` repo.

### Any static host
`./out` is a plain static folder — drop it on Netlify, Cloudflare Pages, S3, or anything else.

---

## 🗺️ Project structure

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
  video.ts          Canvas cinema renderer + MediaRecorder encoding
  storage.ts        IndexedDB gallery persistence
  download.ts       4K upscaling, blob download, clipboard
  presets.ts        The 7 prompts
  styles.ts         Style suffixes, negatives, aspect ratios
  types.ts          Shared types
```

---

## ❓ Notes

- **Video downloads as `.webm` instead of `.mp4`?** Your browser lacks H.264 canvas recording (mostly Firefox).
  Chrome, Edge and Safari produce MP4. WebM uploads fine to YouTube, TikTok and Instagram anyway.
- **First image is slow?** Pollinations cold-starts at 15–40s. Later renders are much faster.
- **Keep the tab visible while rendering video** — browsers throttle background tabs, which slows the capture.

## 📄 License

MIT — do whatever you want with it, including commercial use.
