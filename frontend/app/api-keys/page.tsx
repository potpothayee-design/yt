"use client";

/** API Keys: encrypted key management per capability/provider. */

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { ProviderSettings } from "@/lib/types";
import { Card, SectionTitle, Spinner } from "@/components/ui";

const CAPABILITY_LABELS: Record<string, { label: string; hint: string }> = {
  text: { label: "Text Generation", hint: "OpenAI / Anthropic — script & metadata writing" },
  image: { label: "Image Generation", hint: "OpenAI Images / Stability — scene art" },
  video: { label: "Video Generation", hint: "Pika / Runway — motion clips" },
  voice: { label: "Voice Synthesis", hint: "OpenAI TTS / ElevenLabs / Google — narration voice" },
  music: { label: "Music Generation", hint: "works offline; library provider uses your files" },
};

export default function ApiKeysPage() {
  const [settings, setSettings] = useState<ProviderSettings | null>(null);
  const [keys, setKeys] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const load = async () => {
    try {
      setSettings(await api.get<ProviderSettings>("/api/v1/settings/providers"));
    } catch {
      /* auth guard */
    }
  };

  useEffect(() => {
    load();
  }, []);

  const save = async (capability: string, provider: string) => {
    setBusy(capability);
    try {
      const apiKey = keys[capability];
      await api.put(`/api/v1/settings/providers/${capability}`, {
        provider,
        api_key: apiKey ?? null,
      });
      setKeys((k) => ({ ...k, [capability]: "" }));
      setMsg(`✔ key saved for ${CAPABILITY_LABELS[capability].label} (encrypted at rest)`);
      await load();
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : "save failed");
    } finally {
      setBusy(null);
    }
  };

  const clear = async (capability: string, provider: string) => {
    setBusy(capability);
    try {
      await api.put(`/api/v1/settings/providers/${capability}`, {
        provider,
        api_key: "",
      });
      setMsg(`✔ key removed for ${CAPABILITY_LABELS[capability].label}`);
      await load();
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold">API Keys</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Keys are stored <b>encrypted</b> on the server and never sent to the
          browser again. Local providers work with no keys at all.
        </p>
      </div>

      {msg && (
        <p className="rounded-xl bg-brand-500/10 p-3 text-sm text-brand-700 dark:text-brand-300">
          {msg}
        </p>
      )}

      {!settings ? (
        <Card>
          <p className="text-sm text-slate-400">Loading…</p>
        </Card>
      ) : (
        Object.entries(settings.capabilities).map(([capability, state]) => {
          const info = CAPABILITY_LABELS[capability];
          const needsKey = state.available.find((p) => p.name === state.selected)?.requires_key;
          return (
            <Card key={capability}>
              <SectionTitle
                title={info.label}
                subtitle={info.hint}
                action={
                  <span
                    className={
                      "rounded-full px-2.5 py-1 text-xs font-semibold " +
                      (state.has_key
                        ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400"
                        : "bg-slate-500/15 text-slate-500 dark:text-slate-300")
                    }
                  >
                    {state.has_key ? `key set: ${state.masked_key}` : needsKey ? "key required" : "offline ✔"}
                  </span>
                }
              />
              <div className="flex flex-col gap-2 md:flex-row">
                <input
                  className="input flex-1"
                  type="password"
                  placeholder={
                    state.has_key ? "Enter a new key to replace the stored one" : "Paste API key here"
                  }
                  value={keys[capability] ?? ""}
                  onChange={(e) => setKeys((k) => ({ ...k, [capability]: e.target.value }))}
                  autoComplete="off"
                />
                <div className="flex gap-2">
                  <button
                    className="btn-primary text-xs"
                    disabled={busy === capability || !(keys[capability] ?? "").trim()}
                    onClick={() => save(capability, state.selected)}
                  >
                    {busy === capability ? <Spinner /> : "Save key"}
                  </button>
                  {state.has_key && (
                    <button
                      className="btn-danger text-xs"
                      disabled={busy === capability}
                      onClick={() => clear(capability, state.selected)}
                    >
                      Remove
                    </button>
                  )}
                </div>
              </div>
              {!needsKey && !state.has_key && (
                <p className="mt-2 text-xs text-slate-400">
                  The selected provider ({state.selected}) runs fully offline — no key needed.
                  {state.selected === "local" && capability === "music" &&
                    " Switch to the Library provider to use your own licensed tracks."}
                </p>
              )}
            </Card>
          );
        })
      )}

      <Card>
        <SectionTitle title="Environment-based keys" />
        <p className="text-sm text-slate-500 dark:text-slate-400">
          You can also set keys via environment variables (OPENAI_API_KEY,
          ANTHROPIC_API_KEY, STABILITY_API_KEY, ELEVENLABS_API_KEY, GOOGLE_TTS_API_KEY,
          PIKA_API_KEY, RUNWAY_API_KEY, GEMINI_API_KEY, POLLINATIONS_KEY,
          YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET) — see
          <code>.env.example</code>. Keys saved on
          this page take precedence; in production prefer secrets managers / GitHub
          Secrets over any database.
        </p>
      </Card>
    </div>
  );
}
