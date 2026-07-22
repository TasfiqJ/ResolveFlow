export default function NotFound() {
  return (
    <main className="pageShell" id="main-content">
      <header className="pageIntro">
        <p className="eyebrow">NOT FOUND</p>
        <h1>This recorded artifact does not exist.</h1>
        <p>
          Public pages are pre-generated only for sanitized, checksummed runs.
          Return to the known hero workflow or Replay comparison.
        </p>
      </header>
      <div className="linkRow">
        <a href="demo/">Open Resolve</a>
        <a href="replay/">Open Replay</a>
      </div>
    </main>
  );
}
