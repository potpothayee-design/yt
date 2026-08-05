"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import { Spinner } from "@/components/ui";

export default function LoginPage() {
  const { login, register, devLogin } = useAuth();
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [devAvailable, setDevAvailable] = useState(false);

  useEffect(() => {
    api
      .get<{ dev_login?: boolean }>("/api/v1/health")
      .then((h) => setDevAvailable(Boolean(h.dev_login)))
      .catch(() => setDevAvailable(false));
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, name, password);
      router.replace("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "something went wrong");
    } finally {
      setBusy(false);
    }
  };

  const devSignIn = async () => {
    setBusy(true);
    setError(null);
    try {
      await devLogin();
      router.replace("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "dev sign-in is disabled on this server");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-50 via-white to-candy-yellow/20 p-4 dark:from-slate-950 dark:via-slate-950 dark:to-brand-900/20">
      <div className="card w-full max-w-md p-8">
        <div className="mb-6 text-center">
          <span className="text-4xl">🎨</span>
          <h1 className="mt-2 text-xl font-extrabold">AI Kids Video Studio</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {mode === "login" ? "Welcome back — sign in to continue" : "Create your studio account"}
          </p>
        </div>
        <form onSubmit={submit} className="space-y-4">
          {mode === "register" && (
            <div>
              <label className="label">Your name</label>
              <input
                className="input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                placeholder="Jenna"
              />
            </div>
          )}
          <div>
            <label className="label">Email</label>
            <input
              className="input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@example.com"
              autoComplete="email"
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={mode === "register" ? 8 : 1}
              placeholder={mode === "register" ? "8+ characters" : "••••••••"}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
            />
          </div>
          {error && (
            <p className="rounded-xl bg-rose-500/10 p-3 text-sm text-rose-600 dark:text-rose-400">
              {error}
            </p>
          )}
          <button type="submit" className="btn-primary w-full" disabled={busy}>
            {busy && <Spinner />}
            {mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
        {devAvailable && mode === "login" && (
          <div className="mt-4">
            <div className="flex items-center gap-3 text-xs text-slate-400">
              <span className="h-px flex-1 bg-slate-200 dark:bg-slate-700" />
              or
              <span className="h-px flex-1 bg-slate-200 dark:bg-slate-700" />
            </div>
            <button
              type="button"
              onClick={devSignIn}
              disabled={busy}
              className="btn-secondary mt-3 w-full"
            >
              {busy ? <Spinner /> : null}
              ⚡ Continue as local dev — no email or password
            </button>
            <p className="mt-2 text-center text-xs text-slate-400">
              one-click sign-in for local installs
            </p>
          </div>
        )}
        <p className="mt-4 text-center text-sm text-slate-500 dark:text-slate-400">
          {mode === "login" ? "New to the studio?" : "Already have an account?"}{" "}
          <button
            className="font-semibold text-brand-500 hover:underline"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "Create an account" : "Sign in"}
          </button>
        </p>
      </div>
    </div>
  );
}
