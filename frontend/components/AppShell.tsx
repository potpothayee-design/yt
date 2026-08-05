"use client";

/** Application chrome: sidebar navigation + top bar. Hidden on /login. */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { cx } from "@/lib/utils";
import { ThemeToggle } from "@/components/ThemeToggle";

const NAV = [
  { href: "/", label: "Dashboard", icon: "🏠" },
  { href: "/projects", label: "Projects", icon: "🗂️" },
  { href: "/generator", label: "Video Generator", icon: "🎬" },
  { href: "/assets", label: "Assets", icon: "🧩" },
  { href: "/uploads", label: "Uploads", icon: "🚀" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
  { href: "/logs", label: "Logs", icon: "📜" },
  { href: "/api-keys", label: "API Keys", icon: "🔑" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, loading } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  if (pathname === "/login") return <>{children}</>;

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading studio…</p>
        </div>
      </div>
    );
  }
  if (!user) return null; // redirect handled by AuthProvider

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside
        className={cx(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform dark:border-slate-800 dark:bg-slate-900",
          "md:static md:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex items-center gap-2.5 px-5 py-5">
          <span className="text-2xl">🎨</span>
          <div>
            <p className="text-sm font-bold leading-tight">AI Kids Video</p>
            <p className="text-xs font-medium text-brand-500">Studio</p>
          </div>
        </div>
        <nav className="nice-scroll mt-2 flex-1 space-y-1 overflow-y-auto px-3">
          {NAV.map((item) => {
            const active =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={cx(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition",
                  active
                    ? "bg-brand-500 text-white shadow-sm"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                )}
              >
                <span aria-hidden>{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-slate-200 p-4 dark:border-slate-800">
          <p className="truncate text-xs font-semibold">{user.name}</p>
          <p className="truncate text-xs text-slate-500 dark:text-slate-400">{user.email}</p>
        </div>
      </aside>

      {/* Column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between gap-3 border-b border-slate-200 bg-white/80 px-4 backdrop-blur dark:border-slate-800 dark:bg-slate-900/80 md:px-6">
          <button
            className="btn-secondary px-3 py-2 md:hidden"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Menu"
          >
            ☰
          </button>
          <div className="hidden text-sm text-slate-500 dark:text-slate-400 md:block">
            Made-for-kids educational video production
          </div>
          <div className="flex items-center gap-2">
            <Link href="/generator" className="btn-primary">
              <span>＋</span> New Video
            </Link>
            <ThemeToggle />
          </div>
        </header>
        <main className="nice-scroll min-w-0 flex-1 overflow-y-auto p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
