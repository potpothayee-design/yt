# 📦 Tiny Workers Studio

**Free, unlimited AI generator for "Tiny Workers + Cardboard Puzzle + Pixar" images and videos.**
No credits. No watermark. No login. No paid API. It can't run out — because there's nothing to run out of.

Built with Next.js 14 · TypeScript · Tailwind CSS.

---

## ✨ Features

| | |
|---|---|
| 🖼️ **Text to Image** | Prompt → 4K image. 3 locked-in styles, 9:16 / 16:9 / 1:1, batch up to 4 at a time. |
| 🎬 **Image to Video** | Two free engines: **real AI diffusion motion** (Wan/LTX on free GPUs) or **instant cinematic camera** motion. |
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

**Video — two engines, both free, pick per render.**

**1. Real AI motion (default).** True image-to-video diffusion — objects, characters and materials actually move.
Runs open-source **Wan 2.1 / LTX-Video / SVD** on free community Hugging Face Spaces. No account, no card, no credits.
The honest cost is a **queue**: shared GPUs mean 1–8 minutes, and Spaces sometimes sleep or hit daily quota. The app
tries three Spaces in order before giving up.

**2. Cinematic camera (instant fallback).** Animates your frames on a `<canvas>` with eased dolly/pan/crane/orbit/
handheld moves, crossfades, grain, vignette and fades, recorded via `MediaRecorder` to H.264 MP4. The subject itself
doesn't move — but it renders in seconds, works offline, and **never fails**.

If the AI engines are all busy, the app automatically falls back to camera motion so you always walk away with a clip.

### Why not the "free" video APIs?

Checked and rejected, so you don't have to:

| Option | Verdict |
|---|---|
| Pollinations `/video` (Wan, Veo, Seedance) | **Not free.** Every model is `paid_only`. Costs Pollen credits (~$1/Pollen); the free grant is 1.5 Pollen/week ≈ 3 clips. |
| Kling / Hailuo / Luma / Runway free tiers | Daily credits, watermarks, login, non-commercial. Exactly the treadmill this replaces. |
| HF Inference API (serverless) | Video models aren't reliably served; routes to paid providers. |
| **HF Spaces (Wan/LTX/SVD)** | ✅ **Genuinely free, no login, no watermark** — community GPUs, queued. This is what we use. |

> Nothing you make is ever uploaded to a server of ours — there is no backend at all.

---

## 📦 Deploy

### Vercel (recommended)
Import the repo and hit deploy. Zero configuration — no environment variables required.

```bash
npx vercel --prod
```

### GitHub Pages
A ready-made workflow ships at [`deploy/github-pages.yml`](deploy/github-pages.yml). Activate it with:

```bash
mkdir -p .github/workflows
cp deploy/github-pages.yml .github/workflows/deploy.yml
git add .github/workflows/deploy.yml && git commit -m "ci: enable Pages" && git push
```

Then set **Settings → Pages → Source → GitHub Actions**. See [`deploy/README.md`](deploy/README.md) for details.

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
  aivideo.ts        Real AI motion via free Hugging Face Spaces (Wan/LTX/SVD)
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
- **AI motion says "engines busy"?** Free community GPUs are shared and genuinely run out. Retry in a few minutes,
  or switch to the Cinematic camera engine for an instant result. There is no way to skip the queue without paying.
- **Keep the tab visible while rendering video** — browsers throttle background tabs, which slows the capture.
- **Dev server 500s after running `npm run build`?** The production build overwrites the `.next` folder the dev
  server is watching. Fix: `rm -rf .next && npm run dev`.
- **Rare "blocked pixel access" warning?** If your browser refuses direct access to the generated pixels, the app
  still shows and downloads the image, but it can't be saved to the gallery or animated. Regenerating clears it.

## 📄 License

MIT — do whatever you want with it, including commercial use.
