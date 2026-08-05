# AI Provider Guide

The studio never depends on one vendor. Five capability interfaces
(`app/services/providers/base.py`) define the contracts; each capability has
multiple interchangeable providers. The pipeline consumes identical inputs
(character sheet, scene prompts, durations) no matter which provider is
selected, and **local offline providers always work as a fallback** — if an
external provider lacks an API key, the system logs a warning and degrades to
the local one instead of failing.

## Catalog

| Capability | Provider | Keys | Notes |
| --- | --- | --- | --- |
| Text | `local` Built-in Writer | — | Original curriculum-aware script & metadata engine; offline, deterministic per project seed |
| Text | `openai` OpenAI GPT | `OPENAI_API_KEY` | Guided by knowledge base + strict JSON + originality rules (`gpt-4o-mini` default, configurable via options) |
| Text | `anthropic` Anthropic | `ANTHROPIC_API_KEY` | Same briefs as OpenAI path (`claude-3-5-haiku` default) |
| Image | `local` Built-in Illustrator | — | Procedural storybook scenes: consistent mascot, glyph library, banners |
| Image | `openai` OpenAI Images | `OPENAI_API_KEY` | DALL·E 3 / gpt-image-1 with the full scene prompt + negative prompt |
| Image | `stability` Stability AI | `STABILITY_API_KEY` | SDXL / Stable Image Core, negative prompt + seed support |
| Video | `local` Built-in Motion Engine | — | ffmpeg Ken Burns / pans / float with fade edges; arbitrary lengths |
| Video | `runway` Runway | `RUNWAY_API_KEY` | Image-to-video from the rendered keyframe + motion prompt |
| Video | `pika` Pika | `PIKA_API_KEY` | Text-to-video per scene |
| Voice | `local` Built-in Voice | — | Offline formant synthesizer, exact word timings; espeak if installed |
| Voice | `openai-tts` OpenAI TTS | `OPENAI_API_KEY` | Natural voices (nova/onyx/shimmer map) |
| Voice | `elevenlabs` ElevenLabs | `ELEVENLABS_API_KEY` | Expressive kid-friendly voices |
| Voice | `google-tts` Google Cloud | `GOOGLE_TTS_API_KEY` | Many languages |
| Music | `local` Built-in Composer | — | Original royalty-free loops (marimba/pad/bass/hats) |
| Music | `library` Your library | `MUSIC_LIBRARY_DIR` | Uses tracks YOU have licensed (compliance by construction) |

> Vendor video/TTS APIs evolve. The Runway/Pika clients isolate their payload
> shape in one small method — update that if your account uses a newer schema.

## How consistency survives a provider swap

Both external image providers and video providers receive the same payloads:

1. **Character sheet** embedded in every image prompt (name, species, hex
   colors, accessory, eye style, consistency rules).
2. **Scene prompts** with camera, lighting, palette, composition and style
   tokens.
3. A **global negative prompt** banning morphing, flickering, extra limbs,
   text artifacts, watermark, style drift…
4. **Per-scene seeds** (`sheet_seed + scene_index`) whenever the provider
   supports seeding.

Short-clip providers (5–10 s) are no problem: the pipeline plans one clip per
scene and the composer merges any number of clips with matched crossfades —
continuity comes from the shared keyframe + prompts.

## Configuring

Per user (stored encrypted): **Settings** page selects the provider per
capability; **API Keys** page stores the key. Resolution order at job start:

```
user setting (DB) → environment default → local fallback
```

Environment defaults: `TEXT_PROVIDER`, `IMAGE_PROVIDER`, `VIDEO_PROVIDER`,
`VOICE_PROVIDER`, `MUSIC_PROVIDER` (+ the vendor keys in `.env.example`).

## Music library provider (licensed tracks)

```
mkdir -p /data/music/cheerful /data/music/calm
cp ~/Downloads/my-licensed-track.mp3 /data/music/cheerful/
export MUSIC_LIBRARY_DIR=/data/music
# Settings → music → "Royalty-free Library"
```

Only place tracks you have the rights to use. The track is looped/trimmed to
length and ducked beneath the narration automatically.

## Adding a new provider (e.g., a new TTS vendor)

```python
# app/services/providers/voice/mynewtts.py
from app.services.providers.base import VoiceResult, WordTiming

class MyNewTTSProvider:
    name = "mynewtts"
    label = "MyNewTTS"
    requires_key = True

    def __init__(self, api_key=None, options=None):
        self.api_key = api_key or ""

    def synthesize(self, text, out_path, *, voice="female",
                   language="en", target_duration=None) -> VoiceResult:
        ...  # call the vendor API, save audio to out_path
        return VoiceResult(path=out_path, duration=duration,
                           word_timings=[WordTiming(word=w, start=s, end=e), ...])
```

Register it in `app/services/providers/registry.py` under `"voice"` — done.
The Settings page, key storage, provider test button and pipeline pick it up
automatically.

## Provider test button

`POST /api/v1/settings/providers/{capability}/test` instantiates the selected
provider and performs the cheapest possible verification (e.g. `GET /models`
for OpenAI-style vendors). Local providers always report OK.
