import type { Metadata } from "next";
import Link from "next/link";
import "./styles.css";

export const metadata: Metadata = {
  title: "ResolveFlow — The AI agent release gate",
  description:
    "Tasfiq Jasimuddin engineered ResolveFlow to stress-test enterprise AI agents under failure and turn auditable evidence into a release verdict.",
  openGraph: {
    title: "ResolveFlow — The AI agent release gate",
    description:
      "I built the release gate AI agents are missing. Resolve, replay, verify, and decide what ships.",
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
    title: "ResolveFlow — The AI agent release gate",
    description:
      "I built the release gate AI agents are missing. Resolve, replay, verify, and decide what ships.",
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
          <Link className="brand" href="/" aria-label="ResolveFlow home">
            <span className="brandMark">RF</span>
            <span>
              <b>RESOLVEFLOW</b>
              <small>AI RELEASE SYSTEM</small>
            </span>
          </Link>
          <nav aria-label="Primary navigation">
            <Link href="/replay/">Replay</Link>
            <Link href="/architecture/">Architecture</Link>
            <Link href="/results/">Evidence</Link>
          </nav>
          <a
            className="navAction"
            href="https://github.com/TasfiqJ/ResolveFlow"
          >
            View source ↗
          </a>
        </header>
        {children}
      </body>
    </html>
  );
}
