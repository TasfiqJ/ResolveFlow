import liveSnapshot from "../../../public/snapshots/hero-cohere-live.json";
import recordedSnapshot from "../../../public/snapshots/hero-foundation.json";

const basePath = (process.env.NEXT_PUBLIC_BASE_PATH ?? "").replace(/\/+$/, "");

const runs = {
  [recordedSnapshot.run_id]: {
    snapshot: recordedSnapshot,
    label: "RECORDED RUN · SYNTHETIC FIXTURE",
    shortLabel: "Recorded fixture",
    file: "hero-foundation.json",
  },
  [liveSnapshot.run_id]: {
    snapshot: liveSnapshot,
    label: "LIVE-PROVIDER RUN · SYNTHETIC DATA · NO SHIP",
    shortLabel: "Live-provider run",
    file: "hero-cohere-live.json",
  },
} as const;

export function generateStaticParams() {
  return Object.keys(runs).map((run_id) => ({ run_id }));
}

export default async function RunPage({
  params,
}: {
  params: Promise<{ run_id: string }>;
}) {
  const { run_id } = await params;
  const selected =
    runs[run_id as keyof typeof runs] ?? runs[recordedSnapshot.run_id];
  const { snapshot } = selected;
  const isLive = snapshot.provenance === "live_provider";
  const totalProviderTokens = snapshot.provider_traces.reduce(
    (total, trace) =>
      total + trace.usage.input_tokens + trace.usage.output_tokens,
    0,
  );

  return (
    <main className="pageShell" id="main-content">
      <header className="pageIntro">
        <p className="eyebrow">{selected.label}</p>
        <h1>Audit {snapshot.run_id}</h1>
        <p>
          {isLive
            ? "Cohere Chat, Embed, and Rerank ran live over a labeled synthetic case. This is provider execution evidence, not a quality, customer, connector, or release claim."
            : "This deterministic recorded fixture remains the credential-free baseline for comparison."}
        </p>
      </header>

      <section className="twoColumn" aria-label="Published run comparison">
        {Object.values(runs).map((run) => (
          <article className="panel" key={run.snapshot.run_id}>
            <p className="eyebrow">{run.shortLabel}</p>
            <h2>{run.snapshot.response.summary}</h2>
            <p>
              <b>{run.snapshot.provenance.replaceAll("_", " ")}</b> ·{" "}
              {run.snapshot.generated_at}
            </p>
            {run.snapshot.run_id === snapshot.run_id ? (
              <p>Currently open</p>
            ) : (
              <a href={`${basePath}/runs/${run.snapshot.run_id}/`}>
                Open {run.shortLabel.toLowerCase()}
              </a>
            )}
          </article>
        ))}
      </section>

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
        <span>
          Provider <code>{snapshot.response.provider}</code>
        </span>
      </section>

      <section className="twoColumn">
        <article className="panel">
          <h2>Verified response</h2>
          <p>
            <b>Status:</b> {snapshot.response.status.replaceAll("_", " ")}
          </p>
          <p>
            <b>Route:</b> {snapshot.response.route ?? "No verified route"}
          </p>
          <p>{snapshot.response.summary}</p>
          <h3>Known unknowns</h3>
          <ul>
            {snapshot.response.unknowns.map((unknown) => (
              <li key={unknown}>{unknown}</li>
            ))}
          </ul>
        </article>
        <article className="panel">
          <h2>Action boundary</h2>
          <p>
            <b>{snapshot.action.state.replaceAll("_", " ")}</b> · synthetic
            connector not dispatched
          </p>
          <p>{snapshot.action.summary}</p>
          {snapshot.action.payload_digest ? (
            <p className="hashLine">
              <code>{snapshot.action.payload_digest}</code>
            </p>
          ) : null}
          <p>
            <b>NO SHIP:</b> no real Slack or Jira write was attempted or
            authorized.
          </p>
        </article>
      </section>

      <section className="panel">
        <h2>Verified citations</h2>
        {snapshot.response.citations.length ? (
          <ol className="citationList">
            {snapshot.response.citations.map((citation) => (
              <li key={citation.citation_id}>
                <strong>{citation.title}</strong>
                <p>
                  <code>{citation.source_id}</code> · {citation.locator} ·
                  version {citation.version}
                </p>
                <blockquote>{citation.excerpt}</blockquote>
                <small>{citation.verifier_codes.join(" · ")}</small>
              </li>
            ))}
          </ol>
        ) : (
          <p>No citation passed the deterministic verifier for this run.</p>
        )}
      </section>

      <section className="panel">
        <h2>Provider calls</h2>
        <p>
          {snapshot.provider_traces.length} bounded calls ·{" "}
          {totalProviderTokens.toLocaleString("en-CA")} tokens recorded.
          Provider request and response bodies are represented by hashes;
          credentials and hidden reasoning are excluded.
        </p>
        <ol className="auditList">
          {snapshot.provider_traces.map((trace) => (
            <li key={trace.provider_call_id}>
              <code>{trace.provider_call_id.replace("provider_", "")}</code>
              <div>
                <small>
                  {trace.pass_kind} · {trace.status} · {trace.duration_ms} ms
                </small>
                <strong>{trace.model}</strong>
                <span className="hashLine">request {trace.request_hash}</span>
                <span className="hashLine">
                  response {trace.response_hash ?? "none"}
                </span>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="panel">
        <h2>Full hash-linked audit trace</h2>
        <ol className="auditList">
          {snapshot.trace.map((event) => (
            <li key={event.event_id}>
              <code>{String(event.sequence).padStart(2, "0")}</code>
              <div>
                <small>
                  {event.component} · {event.outcome}
                </small>
                <strong>{event.event_name}</strong>
                <span className="hashLine">
                  previous {event.previous_event_hash ?? "GENESIS"}
                </span>
                <span className="hashLine">event {event.event_hash}</span>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="panel">
        <h2>Integrity and evidence boundary</h2>
        <p>Snapshot content hash</p>
        <p className="hashLine">
          <code>{snapshot.content_hash}</code>
        </p>
        <p>
          Observable application events only. Hidden prompts, hidden reasoning,
          credentials, and restricted evidence are not part of this public
          projection. The incident, customer, rollout, and connector data are
          synthetic; human review and a final release verdict remain pending.
        </p>
        <a href={`${basePath}/snapshots/${selected.file}`}>Download sanitized JSON</a>
      </section>
    </main>
  );
}
