const layers = [
  ["Experience", "Static Next.js routes, snapshot viewer, private review UX"],
  [
    "Application",
    "FastAPI intake, shared Resolve orchestration, local approval state-machine APIs; upstream authentication is not wired",
  ],
  [
    "Evidence",
    "Policy → lexical/vector → fusion → Rerank → bounded agent → verifier",
  ],
  [
    "Effects",
    "Payload-bound approval decision → durable queue → synthetic/staging-only connector",
  ],
];

export default function ArchitecturePage() {
  return (
    <main className="pageShell" id="main-content">
      <header className="pageIntro">
        <p className="eyebrow">ARCHITECTURE</p>
        <h1>The model is never the security boundary.</h1>
        <p>
          Resolve and Replay share one production orchestration path. Replay
          changes frozen inputs and connector behavior, not the controls being
          evaluated. The local approval state machine validates proposal state,
          the exact payload digest, and declared permissions outside the model,
          but it does not authenticate the caller. End-to-end approval identity
          requires a trusted upstream authentication and authorization layer.
        </p>
      </header>
      <section className="architectureFlow" aria-label="System layers">
        {layers.map(([name, detail], index) => (
          <article key={name}>
            <span>{index + 1}</span>
            <div>
              <h2>{name}</h2>
              <p>{detail}</p>
            </div>
          </article>
        ))}
      </section>
      <section className="twoColumn">
        <article className="panel">
          <h2>Trust boundaries</h2>
          <ul>
            <li>Eligibility is materialized before search.</li>
            <li>Retrieved text is data, never authority.</li>
            <li>Verified graph IDs close the second pass.</li>
            <li>
              Proposal state and the exact approval payload are checked outside
              the model; caller identity and permission headers are trusted
              inputs until an upstream identity layer is wired.
            </li>
            <li>Public traces are deterministic redactions.</li>
          </ul>
        </article>
        <article className="panel">
          <h2>Runtime topology</h2>
          <ul>
            <li>Static public web: no credentials or backend dependency.</li>
            <li>Local FastAPI and worker: bounded optional live path.</li>
            <li>PostgreSQL + pgvector: durable state and jobs.</li>
            <li>Slack/Jira: disabled adapters unless explicitly staged.</li>
          </ul>
        </article>
      </section>
    </main>
  );
}
