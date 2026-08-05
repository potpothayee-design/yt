# REST API Reference

Base URL: `/api/v1` · Interactive docs: `http://localhost:8000/docs`
Auth: `Authorization: Bearer <JWT>` on all endpoints except
`auth/*`, `health`, `meta/*`, `youtube/callback`, `jobs/callback/*`.

Errors are `{"detail": "human readable message"}` with sensible status codes.

## Auth

| Method & path | Body | Description |
| --- | --- | --- |
| `POST /auth/register` | `{email, name, password}` | Create account; first user becomes admin. → `{access_token}` |
| `POST /auth/login` | `{email, password}` | → `{access_token}` |
| `GET /auth/me` | — | current user profile |

## Projects

| Method & path | Body / query | Description |
| --- | --- | --- |
| `GET /projects` | `?status=` | list caller's projects |
| `POST /projects` | `{topic, params}` | create draft project |
| `GET /projects/{id}` | — | full detail: knowledge, script, storyboard, prompts, metadata, assets, latest job, media URLs |
| `PATCH /projects/{id}` | `{title?, script?, video_metadata?}` | Preview-page editing; script edits sync engine state for regeneration |
| `DELETE /projects/{id}` | — | delete project + cascade |
| `POST /projects/{id}/generate` | `?runner=local\|github&resume=true` | start full pipeline (202) → Job |
| `POST /projects/{id}/regenerate` | `{target: scene\|thumbnail\|voice\|music\|video, scene_index?, instruction?}` | partial regeneration (202) → Job (`video` = full fresh pipeline) |
| `GET /projects/{id}/jobs` | — | recent jobs |
| `POST /projects/{id}/jobs/{job_id}/cancel` | — | request cooperative cancel |

Generation params (`params`):

```json
{
  "topic": "ABCs",
  "target_age": "3-6 | 7-9 | 10-13",
  "length_seconds": 30,
  "style": "3D Cartoon",
  "animation_type": "playful",
  "voice": "female | male | child",
  "language": "en",
  "music_mood": "cheerful | calm | adventure | bedtime",
  "aspect_ratio": "16:9 | 9:16 | 1:1",
  "quality": "draft | standard | high"
}
```

## Jobs

| Method & path | Description |
| --- | --- |
| `GET /jobs/{id}` | job status + `steps[]` (`{name,label,status,message,started_at,finished_at}`); poll every ~2s for the live tracker |
| `POST /jobs/callback/{id}` | GitHub Actions progress (header `X-Job-Token`) |
| `POST /jobs/callback/{id}/artifact` | multipart artifact receive (same token) |
| `POST /jobs/callback/{id}/complete` | completion signal (same token) |

## Assets

| Method & path | Description |
| --- | --- |
| `GET /assets?project_id=&kind=&limit=` | list with absolute URLs |
| `GET /assets/{id}` | one asset |

Kinds: `image`, `video_clip`, `voice`, `music`, `captions`, `thumbnail`, `final_video`.

## Uploads (YouTube)

| Method & path | Body | Description |
| --- | --- | --- |
| `GET /uploads` | — | upload history |
| `POST /projects/{id}/uploads` | `{confirm: true, privacy, made_for_kids, scheduled_at?, title?, description?, tags?}` | **explicit approval required** (`422` otherwise; `422` if no final video; `422` if YouTube not connected). Uploads run in background with retries. |
| `POST /uploads/{id}/retry` | — | retry a failed upload |
| `POST /uploads/{id}/refresh` | — | poll YouTube processing status |

### The approval contract

1. Backend refuses `confirm=false`.
2. UI requires checking an explicit "I approve this upload" box.
3. Default privacy is `private` (draft). Scheduling passes RFC 3339
   `scheduled_at` and YouTube auto-publishes then.
4. Audience uses `madeForKids` / `selfDeclaredMadeForKids`.

## Settings & providers

| Method & path | Description |
| --- | --- |
| `GET /settings/providers` | catalog + selection + masked key status per capability |
| `PUT /settings/providers/{capability}` | `{provider, api_key?, options?}` set provider/key/options (encrypts key) |
| `POST /settings/providers/{capability}/test` | cheapest validation → `{ok, message}` |

Capabilities: `text | image | video | voice | music`.

## YouTube connection

| Method & path | Description |
| --- | --- |
| `GET /youtube/status` | `{configured, connected, channel}` |
| `GET /youtube/connect` | → `{auth_url}` (Google consent) |
| `GET /youtube/callback?code=&state=` | OAuth redirect target (stores encrypted tokens) |
| `POST /youtube/disconnect` | revoke stored tokens |

## Logs

| Method & path | Description |
| --- | --- |
| `GET /logs?level=&project_id=&limit=` | newest-first audit entries |

## Meta

| Method & path | Description |
| --- | --- |
| `GET /health` | app + ffmpeg versions (public) |
| `GET /meta/provider-catalog` | all providers with flags |
| `GET /meta/pipeline-steps` | step names/labels (tracker) |
| `GET /meta/topic-ideas` | curated topic suggestions |

## Media streaming

Generated files stream from `GET /media/{key}` (local storage) or from the
configured S3/R2 public URL. The dashboard proxies `/media/*` via its
`/backend/*` rewrite so playback is same-origin everywhere.
