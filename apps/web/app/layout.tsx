import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "Nightingale Care Note",
  description: "A provenance-first longitudinal patient Care Note.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
