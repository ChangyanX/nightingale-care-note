import type { Metadata } from "next";
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
