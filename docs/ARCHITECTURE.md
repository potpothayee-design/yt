# Architecture

## System overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                            Browser                                    │
│        Next.js dashboard (React 19, TypeScript, Tailwind)             │
│   Dashboard │ Projects │ Generator │ Assets │ Uploads │ Settings …    │
└───────────────┬──────────────────────────────────────────────────────┘
                │ same-origin /backend/* (Next.js rewrites proxy)
                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     FastAPI backend (uvicorn)                         │
│                                                                       │
│  api/v1 ── auth · projects · jobs · assets · uploads · settings ·     │
│             logs · youtube · meta                                     │
│     │                                                                 │
│     ▼                                                                 │
│  ┌───────────────┐   ┌─────────────────┐   ┌────────────────────┐     │
│  │ Orchestrator  │──▶│ Pipeline Engine │──▶│ Provider Registry   │     │
│  │ (jobs, resume,│   │ (12 steps, pure │   │ text·image·video·   │     │
│  │  cancel, GH)  │   │  filesystem)    │   │ voice·music          │     │
│  └──────┬────────┘   └────────┬────────┘   └─────────┬──────────┘     │
│         │                     │                      │                │
│         ▼                     ▼                      ▼                │
│   ┌───────────┐        ┌────────────┐      external AI APIs (opt.)    │
│   │ SQLAlchemy│        │ Rendering  │      OpenAI · Anthropic ·        │
│   │ SQLite /  │        │ composer • │      Stability · ElevenLabs ·    │
│   │ PostgreSQL│        │ captions • │      Google TTS · Pika · Runway  │
│   └───────────┘        │ thumbnails │                                 │
│                        └─────┬──────┘                                 │
│                              ▼                                        │
│                     ffmpeg (imageio-ffmpeg binary)                    │
│                                                                       │
│  storage ── local disk volume / AWS S3 / Cloudflare R2                │
│  youtube ── OAuth 2.0 + Data API v3 (resumable uploads)               │
└──────────────────────────────────────────────────────────────────────┘
                        ▲
                        │ POST /api/v1/jobs/callback/{id}  (progress + artifacts)
┌───────────────────────┴───────────────────────────────────────────────┐
│ GitHub Actions (generate.yml)  — long-running optional render runner  │
│   python -m app.workers.runner --standalone --topic … --callback-url  │
└──────────────────────────────────────────────────────────────────────┘
```

## Layered backend design

```
api/          → HTTP only: validate input, call services, serialize output
services/     → all business logic
  pipeline/     engine (12 pure steps over a work_dir + state.json)
                orchestrator (DB jobs, progress, assets, resume, cancel,
                              GitHub Actions dispatch & callbacks)
                knowledge (curriculum data), promptbuilder (prompts)
  providers/    capability interfaces + local offline implementations
                + external vendor implementations (thin httpx clients)
  rendering/    ffmpeg composer, caption renderers, thumbnails
  storage/      Storage protocol: local | s3 (R2-compatible)
  youtube/      oauth (token storage encrypted) + client (uploads)
models/       → tables: users, projects, pipeline_jobs, assets,
                provider_settings, upload_records, log_entries
schemas/      → Pydantic request/response validation
core/         → settings, security (PBKDF2, JWT, Fernet), logging,
                rate limiting, error model
workers/      → standalone runner used by GitHub Actions
```

## Key invariants

1. **No upload without approval.** The pipeline never calls YouTube.
   Uploads are a separate flow: `POST /projects/{id}/uploads` requires
   `confirm=true`, the video must be complete, and the user must have
   connected YouTube OAuth. The 13th pipeline step "upload" only ever
   reports **Pending Approval**.
2. **Persistence-agnostic engine.** `PipelineEngine` works on a directory
   with a `state.json` mirror. The DB orchestrator and the GitHub Actions
   runner drive the exact same engine via a `progress` callback — so
    jobs are resumable after interruption, restart, or dispatch to a
   different runner.
3. **Provider isolation.** The pipeline talks to five capability
   interfaces. Selecting a different provider (Settings page) changes
   which class is instantiated — nothing else. Local providers make the
   whole system work offline; external providers consume the identical
   character-sheet-embedded prompts.
4. **Character consistency** is data-driven: the character sheet is a
   deterministic function of `(topic, project_id)`. Every scene prompt,
   local render, thumbnail and card derives from it.
5. **Timing consistency:** narration is synthesized before clips, clips
   are rendered to fill each scene's slot, and the composer extends a
   clip's tail frame if narration runs long (`tpad=clone`) so audio and
   video never drift.

## Rendering pipeline detail (the "editing" step)

```
scene clips (any provider) ──▶ normalize (scale/crop/fps/tpad) ──▶ xfade chain
intro/outro cards (Pillow)  ──▶ zoompan clips ──────────────────▶     │
                                                                      ▼
scene voice wavs ──▶ adelay(scene_start) ──▶ amix ───────────┐   final video
music wav ──▶ aloop ──▶ volume ──────────────────────────────┤   (720p/1080p,
                                                             ├─▶ loudnorm(-14 LUFS)
caption PNGs (word highlight, Pillow) ──▶ overlay-between ───┘   faststart MP4,
                                                                 SRT/ASS files)
```

- All in a single ffmpeg pass after per-clip normalization (robust to any
  external clip format).
- `imageio-ffmpeg` provides the ffmpeg binary — no OS packages needed,
  identical behavior in Docker, CI and servers.

## Scaling path

| Today | Horizontal scale path |
| --- | --- |
| In-process background threads (semaphore-bounded) | Move `orchestrator._run_local` body into Celery/RQ workers on Redis; steps are already side-effect-free |
| Local sqlite | `DATABASE_URL` → PostgreSQL (compose prod overlay) |
| Local disk media | `STORAGE_BACKEND=s3` (+ CDN URL) — one config switch, assets served from R2/S3 |
| Poll-based progress | Swap `job_out` polling for WebSocket/SSE on the same data |
| Single uvicorn | `uvicorn --workers N` behind nginx/Cloudflare; jobs run in the GitHub Actions runner or Celery fleet |

## Security architecture

- JWT access tokens (HS256), PBKDF2-HMAC-SHA256 password hashing, 600k iterations.
- Per-user provider keys encrypted with Fernet derived from `SECRET_KEY`,
  masked in all responses (`sk-t…abcd`).
- Rate limiting middleware (per-IP sliding window), security headers,
  `X-Frame-Options`, `nosniff`, referer policy.
- The GitHub Actions callback channel is authenticated with a shared
  `JOB_CALLBACK_SECRET` header.
- All user input validated by Pydantic schemas; SQL via SQLAlchemy ORM only.
