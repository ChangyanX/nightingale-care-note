import type { Metadata } from "next";
import "@fontsource/dm-sans/300.css";
import "@fontsource/dm-sans/400.css";
import "@fontsource/dm-sans/500.css";
import "@fontsource/dm-sans/600.css";
import "@fontsource/dm-sans/700.css";
import "./styles.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Nightingale Care Note",
  description: "A provenance-first longitudinal patient Care Note.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
