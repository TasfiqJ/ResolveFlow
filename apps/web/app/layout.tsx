import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "ResolveFlow Replay",
  description:
    "A snapshot-first deployment gate that replays a synthetic enterprise incident under controlled failures.",
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
            <span>
              ResolveFlow <strong>Replay</strong>
            </span>
          </a>
          <nav aria-label="Primary navigation">
            <a href="demo/">Resolve</a>
            <a href="replay/">Replay</a>
            <a href="results/">Results</a>
            <a href="architecture/">Architecture</a>
            <a href="methodology/">Method</a>
            <a href="about/">About</a>
          </nav>
          <div className="recorded">
            <span aria-hidden="true" /> Recorded run
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
