import type { Metadata } from "next";
import Link from "next/link";
import "./styles.css";

export const metadata: Metadata = {
  title: "ResolveFlow — Static AI safety engineering case study",
  description:
    "A credential-free GitHub Pages case study of ResolveFlow: a locally implemented AI-agent release gate with recorded evidence, Replay, and explicit limits.",
  openGraph: {
    title: "ResolveFlow — AI agent release-gate case study",
    description:
      "A static, evidence-led case study of ResolveFlow's locally implemented agent-safety system.",
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
    title: "ResolveFlow — AI agent release-gate case study",
    description:
      "A static, evidence-led case study of ResolveFlow's locally implemented agent-safety system.",
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
            <Link href="/queue/">Queue</Link>
            <Link href="/replay/">Replay</Link>
            <Link href="/architecture/">Architecture</Link>
            <Link href="/results/">Evidence</Link>
            <Link href="/approvals/">Approvals</Link>
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
