"use client";

import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    setDark(document.documentElement.classList.contains("dark"));
  }, []);

  const toggle = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    try {
      window.localStorage.setItem("studio.theme", next ? "dark" : "light");
    } catch {
      /* private mode */
    }
  };

  return (
    <button
      onClick={toggle}
      aria-label="Toggle dark mode"
      className="btn-secondary h-10 w-10 rounded-xl px-0 text-base"
      title={dark ? "Switch to light mode" : "Switch to dark mode"}
    >
      {dark ? "☀️" : "🌙"}
    </button>
  );
}
