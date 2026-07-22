import snapshot from "../../../public/snapshots/hero-foundation.json";

export function generateStaticParams() {
  return [{ run_id: "run_hero_foundation_001" }];
}

export default function RunPage() {
  return (
    <main className="pageShell" id="main-content">
      <header className="pageIntro">
        <p className="eyebrow">RECORDED RUN · SYNTHETIC</p>
        <h1>Audit {snapshot.run_id}</h1>
        <p>
          Observable application events only. Hidden prompts, reasoning,
          credentials, and restricted evidence are not part of this public
          projection.
        </p>
      </header>
      <section className="provenance wide">
        <span>
          Generated <code>{snapshot.generated_at}</code>
        </span>
        <span>
          Build <code>{snapshot.build_id}</code>
        </span>
        <span>
          Commit <code>{snapshot.commit}</code>
        </span>
        <span>
          Policy <code>{snapshot.model_policy}</code>
        </span>
        <span>
          Corpus <code>{snapshot.corpus_version}</code>
        </span>
      </section>
      <section className="twoColumn">
        <article className="panel">
          <h2>Verified response</h2>
          <p>
            <b>Route:</b> {snapshot.response.route}
          </p>
          <p>{snapshot.response.summary}</p>
          <h3>Known unknown</h3>
          <p>{snapshot.response.unknowns[0]}</p>
        </article>
        <article className="panel">
          <h2>Action boundary</h2>
          <p>
            <b>{snapshot.action.state.replaceAll("_", " ")}</b> · synthetic
            connector not dispatched
          </p>
          <p>{snapshot.action.summary}</p>
          <p className="hashLine">
            <code>{snapshot.action.payload_digest}</code>
          </p>
        </article>
      </section>
      <section className="panel">
        <h2>Chronological trace</h2>
        <ol className="auditList">
          {snapshot.trace.map((event) => (
            <li key={event.event_id}>
              <code>{String(event.sequence).padStart(2, "0")}</code>
              <div>
                <small>
                  {event.component} · {event.outcome}
                </small>
                <strong>{event.event_name}</strong>
              </div>
            </li>
          ))}
        </ol>
      </section>
      <section className="panel">
        <h2>Integrity</h2>
        <p>Snapshot content hash</p>
        <p className="hashLine">
          <code>{snapshot.content_hash}</code>
        </p>
        <a href="snapshots/hero-foundation.json">Download sanitized JSON</a>
      </section>
    </main>
  );
}
