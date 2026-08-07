# Setup Guide

Three ways to use this. Pick one — you don't need all three.

---

## ✅ Option 1 — Use it right now (nothing to set up)

**It's already running.** Open the live preview in your Arena sidebar and start generating.

Nothing to install, no account, no keys. This is the fastest way to test it.

⚠️ **One catch:** the preview only stays alive while this Arena session is open.
For a permanent link you can share and use on your phone, do Option 2.

---

## 🌐 Option 2 — Put it online permanently (recommended, ~3 minutes)

No terminal, no code. This gives you a real URL like `tiny-workers-studio.vercel.app`
that works forever, on any device.

✅ **The code is already merged into `main`** — nothing to do first, just deploy.

1. Go to **[vercel.com/new](https://vercel.com/new)**
2. Sign in with **GitHub** (free, no card)
3. Click **Import** next to your `yt` repository
4. Change nothing. Click **Deploy**
5. Wait ~1 minute → you get your live URL

**Do not add any environment variables.** There are none. It works as-is.

### Got a 404 after deploying?

That means Vercel built the repo *before* the app code reached `main`. The fix is to
redeploy — it does **not** mean anything is broken:

1. Open your project on Vercel → **Deployments**
2. Click the **⋯** menu on the most recent one → **Redeploy**
3. Make sure **Use existing Build Cache** is **unchecked**

Alternatively just delete the Vercel project and re-import it. Either way works.

### Updating later
Any push to `main` redeploys automatically. Nothing else to do.

---

## 💻 Option 3 — Run on your own computer

Only needed if you want to edit the code.

**First install [Node.js](https://nodejs.org)** (LTS version), then:

```bash
git clone https://github.com/potpothayee-design/yt.git
cd yt
npm install
npm run dev
```

Open <http://localhost:3000>.

No `.env` file needed. The `.env.example` is entirely optional.

---

## 🎬 How to actually use it

### Make an image
1. **Text to Image** tab
2. Tap a viral preset (loads prompt + style + aspect automatically), or write your own
3. Choose **9:16** for Shorts/TikTok/Reels
4. **Generate** → first one takes 15–40s (cold start), later ones are faster
5. **4K PNG** to download

### Make a video
1. **Animate** under any image (or upload your own in the **Image to Video** tab)
2. Pick your engine:

| Engine | Speed | Motion |
|---|---|---|
| ✨ **Real AI motion** | 1–8 min (queued) | Objects genuinely move — hammers swing, cardboard flexes |
| 🎥 **Cinematic camera** | ~10 seconds | Camera moves over a still; subject itself doesn't move |

3. Write a motion prompt, set duration (5–8s)
4. **Generate** → **Download**

**Tip:** use Cinematic camera while experimenting, then re-run your best shots
through Real AI motion.

Everything saves to the **Gallery** on your device and survives a refresh.

---

## ❓ Troubleshooting

**"All free AI motion engines are busy"**
Real. Free community GPUs are shared and do run out. Wait a few minutes, or use
Cinematic camera. There's no way to skip the queue without paying — that's the honest
trade-off of free.

**Video downloads as `.webm`, not `.mp4`**
Your browser lacks H.264 recording (usually Firefox). Use Chrome, Edge or Safari.
WebM uploads fine to YouTube, TikTok and Instagram regardless.

**First image is slow**
Pollinations cold-starts. Normal. Subsequent renders are quicker.

**Dev server shows an error after `npm run build`**
The build overwrites the folder the dev server watches:
```bash
rm -rf .next && npm run dev
```

**Nothing generates at all**
Check your internet. Some office/school networks block these AI endpoints —
try mobile data.

---

## 💰 Cost check

| | |
|---|---|
| Images (Pollinations Flux) | Free, unlimited, no key |
| AI motion (HF Spaces: Wan/LTX/SVD) | Free, no account, queued |
| Camera motion | Free, runs on your device |
| Vercel hosting | Free tier is plenty |
| Watermarks | None |
| Login | None |

No credit card anywhere. Nothing to run out.
