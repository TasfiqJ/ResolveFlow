import type { Metadata } from "next";
import Link from "next/link";
import "./styles.css";

export const metadata: Metadata = {
  title: "ResolveFlow — Cohere-powered AI release gate",
  description:
    "A credential-free case study of a Cohere-powered AI-agent release gate with recorded Command A+, Embed v4, Rerank v4, Replay, and explicit limits.",
  openGraph: {
    title: "ResolveFlow — Cohere-powered AI release gate",
    description:
      "A recorded, evidence-led case study using Command A+, Embed v4, Rerank v4, and application-enforced safety controls.",
    url: "https://tasfiqj.github.io/ResolveFlow/",
    siteName: "ResolveFlow",
    images: [
      {
        url: "https://tasfiqj.github.io/ResolveFlow/og-static-case-study.png",
        width: 1732,
        height: 909,
        alt: "ResolveFlow static AI safety case study",
      },
    ],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "ResolveFlow — Cohere-powered AI release gate",
    description:
      "A recorded, evidence-led Cohere integration with application-enforced safety controls.",
    images: ["https://tasfiqj.github.io/ResolveFlow/og-static-case-study.png"],
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
              <small>STATIC TECHNICAL CASE STUDY</small>
            </span>
          </Link>
          <nav aria-label="Primary navigation">
            <Link href="/demo/">Demo</Link>
            <Link href="/replay/">Replay</Link>
            <Link href="/cohere/">Cohere</Link>
            <Link href="/results/">Evidence</Link>
            <Link href="/architecture/">Architecture</Link>
            <Link href="/about/">About</Link>
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
