# Deployment Guide

The studio is designed to run from any browser — no local PC required.
Pick the pieces that fit:

| Component | Options |
| --- | --- |
| Frontend | Vercel, Docker (any host), static+node platforms |
| Backend | Render, Fly.io, Railway, any Docker host/VPS |
| Database | SQLite (small/self-hosted) or managed PostgreSQL |
| Storage | Docker volume, AWS S3, Cloudflare R2 |
| CDN/TLS | Cloudflare in front of anything |

---

## 1. Docker Compose (VPS / any Docker host) — simplest production

```bash
git clone <repo> && cd yt
cp .env.example .env
# REQUIRED edits: SECRET_KEY (openssl rand -hex 32), POSTGRES_PASSWORD
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

You get: frontend `:3000`, backend `:8000`, PostgreSQL `db`, named volumes
`studio-data` (SQLite fallback + media) and `pg-data`.

Put Cloudflare (proxied) or any TLS-terminating reverse proxy in front of the
frontend; the frontend proxies `/backend/*` to the backend internally
(`API_PROXY_TARGET=http://backend:8000`).

### Backups

```bash
# Postgres logical backup
docker compose exec db pg_dump -U studio studio > backup-$(date +%F).sql
# Media backup
docker run --rm -v yt_studio-data:/data -v $PWD:/b alpine tar czf /b/media-$(date +%F).tgz -C /data media
```

Run backups via cron; upload to R2/S3 for off-site copies.

---

## 2. Split hosting: Vercel (frontend) + Render (backend)

### Backend on Render

1. New → Web Service → connect repo.
2. Root dir `backend`, build `pip install -r requirements.txt`,
   start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Set env vars: `SECRET_KEY`, `DATABASE_URL` (Render Postgres),
   `STORAGE_BACKEND`, provider keys, `YOUTUBE_*`.
4. Health check path: `/api/v1/health`.
5. Add a Render Disk mounted at `/data` (set `MEDIA_ROOT=/data/media`) **or**
   use S3/R2 so media survives restarts.

> Note: offline video rendering is CPU-bound and takes ~1–5 min for short
> drafts — use Render's "Standard" plan or higher for smooth previews, or
> dispatch long renders to GitHub Actions (see below).

### Frontend on Vercel

1. Import repo, root dir `frontend`.
2. Env var `API_PROXY_TARGET=https://your-backend.onrender.com`.
3. Deploy. The Next.js rewrites proxy all `/backend/*` calls — the browser
   never sees the backend URL and CORS stays simple.

### CORS

Set `CORS_ORIGINS=https://your-vercel-app.vercel.app` on the backend.

---

## 3. Fly.io

```bash
fly launch --dockerfile backend/Dockerfile --name studio-api
fly volumes create studio_data --size 5    # media + sqlite
# in fly.toml mounts: destination = "/data"
fly secrets set SECRET_KEY=... DATABASE_URL=sqlite:////data/studio.db MEDIA_ROOT=/data/media
fly deploy
```

Frontend: Vercel as above with `API_PROXY_TARGET=https://studio-api.fly.dev`.

## 4. Railway

Create a project from the repo's `backend/Dockerfile`, add a PostgreSQL plugin,
set the same env vars (`DATABASE_URL` is injected by Railway), attach a volume
for `/data`. Frontend on Vercel as above.

## 5. Cloudflare R2 (storage) + CDN

1. Create an R2 bucket + API token.
2. Env:
   ```
   STORAGE_BACKEND=s3
   S3_BUCKET=studio-media
   S3_ENDPOINT_URL=https://<accountid>.r2.cloudflarestorage.com
   S3_ACCESS_KEY_ID=...
   S3_SECRET_ACCESS_KEY=...
   S3_PUBLIC_BASE_URL=https://media.yourdomain.com   # custom domain or r2.dev URL
   ```
3. All generated assets stream via the CDN (`storage.url()`).

## 6. GitHub Actions as the render farm

For heavy videos (long duration / high quality) the dashboard can dispatch
renders to GitHub Actions:

1. Create a fine-grained PAT with `actions:write` on this repo → set as the
   backend env `GITHUB_DISPATCH_TOKEN`.
2. Set `GITHUB_REPOSITORY=owner/repo` and `PUBLIC_API_URL=https://your-api`.
3. Repo secrets: `STUDIO_JOB_CALLBACK_SECRET` — must equal the backend's
   `JOB_CALLBACK_SECRET` env var.
4. Optionally add provider keys as repo secrets (`OPENAI_API_KEY`,
   `ELEVENLABS_API_KEY`, …) to use them inside Actions runners.
5. In the Generator choose **Runner: GitHub Actions**. Progress streams into
   the dashboard; artifacts (MP4, thumbnails, captions, state) upload back via
   the authenticated callback endpoints, and also appear as workflow artifacts.

## 7. Health, monitoring, logs

- `GET /api/v1/health` → app version + ffmpeg build (use for uptime checks).
- The Logs page queries the `log_entries` table; containers also log to stdout.
- Sentry: set `SENTRY_DSN` in future versions and plug it into `core/logging.py`.

## 8. Production checklist

- [ ] `SECRET_KEY` is a random 32+ byte value (and never committed)
- [ ] `DATABASE_URL` points to managed PostgreSQL with backups
- [ ] `STORAGE_BACKEND=s3` or a mounted persistent volume for media
- [ ] `CORS_ORIGINS` restricted to your frontend origin
- [ ] `YOUTUBE_CLIENT_ID/SECRET` configured (docs/YOUTUBE_SETUP.md)
- [ ] `JOB_CALLBACK_SECRET` + PAT configured if using the Actions runner
- [ ] TLS enabled (Cloudflare proxy or platform TLS)
- [ ] Uptime check on `/api/v1/health`
- [ ] Backup cron for DB + media
