import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "ResolveFlow — Know when an AI agent is safe to ship",
  description:
    "ResolveFlow solves a workplace incident, replays the same AI agent under failure, and turns the evidence into a clear release verdict.",
  openGraph: {
    title: "ResolveFlow — Know when an AI agent is safe to ship",
    description:
      "Resolve one incident. Replay the same AI agent under failure. Gate the release with evidence.",
    url: "https://tasfiqj.github.io/ResolveFlow/",
    siteName: "ResolveFlow",
    images: [
      {
        url: "https://tasfiqj.github.io/ResolveFlow/og.png",
        width: 1732,
        height: 909,
        alt: "ResolveFlow release-gate overview",
      },
    ],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "ResolveFlow — Know when an AI agent is safe to ship",
    description:
      "Resolve one incident. Replay the same AI agent under failure. Gate the release with evidence.",
    images: ["https://tasfiqj.github.io/ResolveFlow/og.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <base href={`${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/`} />
      </head>
      <body>
        <a className="skipLink" href="#main-content">
          Skip to content
        </a>
        <header className="topbar">
          <a className="brand" href="" aria-label="ResolveFlow Replay home">
            <span className="brandMark">RF</span>
            <span>ResolveFlow</span>
          </a>
          <nav aria-label="Primary navigation">
            <a href="#what-it-does">What it does</a>
            <a href="#how-it-works">How it works</a>
            <a href="#proof">Proof &amp; limits</a>
          </nav>
          <a className="navAction" href="#demo">
            See the demo
          </a>
        </header>
        {children}
      </body>
    </html>
  );
}
