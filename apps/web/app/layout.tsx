import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "ResolveFlow Replay",
  description: "A snapshot-first deployment gate for enterprise agents.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
