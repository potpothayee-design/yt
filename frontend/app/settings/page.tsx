"use client";

/** Settings: provider selection, YouTube connection, preferences. */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { ProviderSettings, YouTubeStatus } from "@/lib/types";
import { Card, SectionTitle, Spinner } from "@/components/ui";

const CAPABILITY_LABELS: Record<string, string> = {
  text: "Text Generation (scripts & metadata)",
  image: "Image Generation (scene art)",
  video: "Video Generation (clips)",
  voice: "Voice Synthesis (narration)",
  music: "Music Generation (background)",
};

export default function SettingsPage() {
  const [settings, setSettings] = useState<ProviderSettings | null>(null);
  const [yt, setYt] = useState<YouTubeStatus | null>(null);
  const [ytEmail, setYtEmail] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [testing, setTesting] = useState<string | null>(null);
  const router = useRouter();

  const load = async () => {
    try {
      setSettings(await api.get<ProviderSettings>("/api/v1/settings/providers"));
      setYt(await api.get<YouTubeStatus>("/api/v1/youtube/status"));
    } catch {
      /* handled by auth guard */
    }
  };

  useEffect(() => {
    load();
  }, []);

  const selectProvider = async (capability: string, provider: string) => {
    try {
      await api.put(`/api/v1/settings/providers/${capability}`, { provider });
      setMsg(`✔ ${CAPABILITY_LABELS[capability]} → switched to '${provider}'`);
      await load();
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : "update failed");
    }
  };

  const test = async (capability: string) => {
    setTesting(capability);
    try {
      const result = await api.post<{ ok: boolean; message: string }>(
        `/api/v1/settings/providers/${capability}/test`
      );
      setMsg(`${result.ok ? "✔" : "✖"} ${result.message}`);
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : "test failed");
    } finally {
      setTesting(null);
    }
  };

  const connectYouTube = async () => {
    try {
      const q = ytEmail.trim() ? `?email=${encodeURIComponent(ytEmail.trim())}` : "";
      const resp = await api.get<{ auth_url: string }>(`/api/v1/youtube/connect${q}`);
      window.location.href = resp.auth_url;
    } catch (err) {
      setMsg(err instanceof ApiError ? err.message : "could not start YouTube connect");
    }
  };

  const disconnectYouTube = async () => {
    await api.post("/api/v1/youtube/disconnect");
    setMsg("✔ YouTube disconnected");
    await load();
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold">Settings</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Choose AI providers per capability and connect your YouTube channel.
          API keys are managed on the{" "}
          <button className="font-semibold text-brand-500 hover:underline" onClick={() => router.push("/api-keys")}>
            API Keys page
          </button>
          .
        </p>
      </div>

      {msg && (
        <p className="rounded-xl bg-brand-500/10 p-3 text-sm text-brand-700 dark:text-brand-300">
          {msg}
        </p>
      )}

      <Card>
        <SectionTitle
          title="AI Providers"
          subtitle="Switch providers without changing anything else — the pipeline adapts"
        />
        {!settings ? (
          <p className="py-4 text-sm text-slate-400">Loading…</p>
        ) : (
          <div className="space-y-4">
            {Object.entries(settings.capabilities).map(([capability, state]) => (
              <div
                key={capability}
                className="flex flex-col gap-3 rounded-2xl bg-slate-50 p-4 dark:bg-slate-800/50 md:flex-row md:items-center"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-bold">{CAPABILITY_LABELS[capability]}</p>
                  <p className="truncate text-xs text-slate-400">
                    selected: {state.selected}
                    {state.has_key ? ` • key: ${state.masked_key}` : " • no key (offline/local mode)"}
                  </p>
                </div>
                <select
                  className="input max-w-56"
                  value={state.selected}
                  onChange={(e) => selectProvider(capability, e.target.value)}
                >
                  {state.available.map((p) => (
                    <option key={p.name} value={p.name}>
                      {p.label}
                      {p.requires_key ? " 🔑" : " (offline)"}
                    </option>
                  ))}
                </select>
                <button
                  className="btn-secondary text-xs"
                  disabled={testing === capability}
                  onClick={() => test(capability)}
                >
                  {testing === capability ? <Spinner /> : "Test"}
                </button>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card>
        <SectionTitle title="YouTube Connection" subtitle="OAuth login — uploads happen only after your approval" />
        <div className="flex flex-col items-start gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm">
              Status:{" "}
              <b className={yt?.connected ? "text-emerald-500" : "text-amber-500"}>
                {yt?.connected ? `Connected${yt.channel ? ` — ${yt.channel}` : ""}` : "Not connected"}
              </b>
            </p>
            {!yt?.configured && (
              <p className="mt-1 max-w-lg text-xs text-amber-600 dark:text-amber-400">
                The server needs YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET to enable
                OAuth. See docs/YOUTUBE_SETUP.md for the 5-minute setup.
              </p>
            )}
          </div>
          {yt?.connected ? (
            <button className="btn-danger text-xs" onClick={disconnectYouTube}>
              Disconnect
            </button>
          ) : (
            <div className="flex w-full flex-col gap-2 md:w-auto">
              <input
                className="input w-full md:w-72"
                type="email"
                placeholder="channel-owner@gmail.com (optional)"
                value={ytEmail}
                onChange={(e) => setYtEmail(e.target.value)}
              />
              <button className="btn-primary text-xs" onClick={connectYouTube} disabled={!yt?.configured}>
                Connect YouTube Channel
              </button>
              <p className="max-w-xs text-xs text-slate-400">
                Google shows an account picker — choose the Gmail that owns your channel.
              </p>
            </div>
          )}
        </div>
      </Card>

      <Card>
        <SectionTitle title="Compliance & Safety" />
        <ul className="list-inside list-disc space-y-1.5 text-sm text-slate-600 dark:text-slate-300">
          <li>All uploads require your explicit approval — nothing is automatic.</li>
          <li>Videos default to <b>private drafts</b>; scheduling sets publish time via YouTube.</li>
          <li>Audience is set to <b>made for kids</b> (COPPA) by default.</li>
          <li>A synthetic-media disclosure is included in descriptions (fully animated content, no real people or events).</li>
          <li>Music is original/royalty-free; the Library provider only uses tracks you supply.</li>
          <li>API keys are stored encrypted and never exposed to the browser.</li>
        </ul>
      </Card>
    </div>
  );
}
