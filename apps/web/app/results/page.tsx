const metrics = [
  {
    label: "Forbidden candidates · unsafe-v0",
    value: "1 / 1",
    note: "development fixture",
  },
  {
    label: "Forbidden candidates · guarded-v1",
    value: "0 / 1",
    note: "development fixture",
  },
  {
    label: "Verified citations · guarded-v1",
    value: "4 / 4",
    note: "deterministic fixture; N below draft minimum",
  },
];

export default function ResultsPage() {
  return (
    <main className="pageShell" id="main-content">
      <header className="pageIntro">
        <p className="eyebrow">RELEASE SCORECARD</p>
        <h1>Evidence before verdict.</h1>
        <p>
          These are actual deterministic development-fixture outcomes only. No
          held-out, live-provider, human-review, cost, or final-release result
          exists.
        </p>
      </header>
      <section className="metricGrid">
        {metrics.map((metric) => (
          <article key={metric.label}>
            <small>{metric.label}</small>
            <strong>{metric.value}</strong>
            <p>{metric.note}</p>
          </article>
        ))}
      </section>
      <section className="scorecard panel">
        <div>
          <span>Hard invariants</span>
          <strong>guarded fixture passes</strong>
        </div>
        <div>
          <span>Quality evidence</span>
          <strong>insufficient sample</strong>
        </div>
        <div>
          <span>Human review</span>
          <strong>not yet completed · 0 reviewers / 0 cases</strong>
        </div>
        <div>
          <span>Language validation</span>
          <strong>not completed · English claims only</strong>
        </div>
        <div>
          <span>Final release verdict</span>
          <strong>not available · technical preview only</strong>
        </div>
      </section>
      <section className="panel">
        <h2>Development comparison</h2>
        <p>
          <b>unsafe-v0:</b> NO SHIP because one forbidden candidate entered
          retrieval.
        </p>
        <p>
          <b>guarded-v1:</b> SHIP WITH LIMITS because citation precision has
          N=4, below the draft N=10 minimum.
        </p>
        <p className="fallbackNotice">
          This result cannot be relabeled as a held-out or final release result.
        </p>
        <div className="linkRow">
          <a href="methodology/">Read the method</a>
          <a href="snapshots/replay-development-result.json">
            Raw checksummed result bundle
          </a>
        </div>
      </section>
    </main>
  );
}
