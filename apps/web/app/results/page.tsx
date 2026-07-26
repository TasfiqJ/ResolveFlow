import Link from "next/link";
import integrity from "../../public/snapshots/evaluation-integrity-audit.json";
import result from "../../public/snapshots/replay-development-result.json";

const hardMetrics = result.candidate.metrics.filter(
  (metric) => metric.family === "hard_invariant",
);
const observedHardMetrics = hardMetrics.filter(
  (metric) => metric.evidence_status === "observed",
);

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
    label: "Evidence-backed hard invariants",
    value: `${observedHardMetrics.length} / ${hardMetrics.length}`,
    note: "unexercised controls are not counted as passes",
  },
  {
    label: "Unique semantic truth templates",
    value: `${integrity.unique_semantic_truth_count} / ${integrity.catalog_entry_count}`,
    note: "36 draft IDs currently duplicate one template",
  },
  {
    label: "Security-matrix full Replay executions",
    value: `${integrity.security_matrix_full_replay_execution_count} / ${integrity.security_matrix_declared_count}`,
    note: "declared matrix cells are not execution evidence",
  },
  {
    label: "Stored attack payload controls",
    value: `${integrity.attack_payload_control_pass_count} / ${integrity.attack_payload_control_execution_count}`,
    note: "deterministic detector executions, not full Replays",
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
          <strong>
            {observedHardMetrics.length}/{hardMetrics.length} observed · NO SHIP
          </strong>
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
          <b>guarded-v1:</b> NO SHIP. The role-downgrade authorization control
          passes, but action dispatch was not exercised, public credential
          absence was not independently verified, held-out data is unlocked, and
          the draft truth catalog contains duplicate semantic templates.
        </p>
        <p className="fallbackNotice">
          A missing observation is now release-blocking evidence, not a zero
          failure.
        </p>
        <div className="linkRow">
          <Link href="/methodology/">Read the method</Link>
          <Link href="/snapshots/replay-development-result.json">
            Raw checksummed result bundle
          </Link>
          <Link href="/snapshots/evaluation-integrity-audit.json">
            Dataset integrity audit
          </Link>
        </div>
      </section>
    </main>
  );
}
