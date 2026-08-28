"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createContext, useContext, useEffect, useState } from "react";

type Theme = "light" | "dark";
const ThemeContext = createContext<{ theme: Theme; setTheme: (theme: Theme) => void } | null>(null);

export function useTheme() {
  const value = useContext(ThemeContext);
  if (!value) throw new Error("useTheme must be used within Providers");
  return value;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () => new QueryClient({ defaultOptions: { queries: { staleTime: 15_000, retry: 1 } } }),
  );
  const [theme, setThemeState] = useState<Theme>("light");

  useEffect(() => {
    const saved = localStorage.getItem("nightingale-theme");
    const initial = saved === "light" || saved === "dark"
      ? saved
      : window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    document.documentElement.dataset.theme = initial;
    document.documentElement.dataset.appReady = "true";
    queueMicrotask(() => setThemeState(initial));
  }, []);

  function setTheme(next: Theme) {
    setThemeState(next);
    document.documentElement.dataset.theme = next;
    localStorage.setItem("nightingale-theme", next);
  }

  return <QueryClientProvider client={queryClient}><ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider></QueryClientProvider>;
}
