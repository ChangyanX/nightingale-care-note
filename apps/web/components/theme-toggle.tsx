"use client";

import { useTheme } from "@/app/providers";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const dark = theme === "dark";
  return <button className="icon-button" type="button" aria-label={dark ? "Use light theme" : "Use dark theme"} aria-pressed={dark} onClick={() => setTheme(dark ? "light" : "dark")}><span aria-hidden="true">{dark ? "☀" : "☾"}</span><span className="sr-only">Theme</span></button>;
}
