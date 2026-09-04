import Link from "next/link";
import ab from "../../public/snapshots/ab-site-current.json";
import integrity from "../../public/snapshots/evaluation-integrity-audit.json";
import result from "../../public/snapshots/replay-development-result.json";

const abBuilds = ab.builds as string[];
const abByBuild = ab.by_build as Record<
  string,
  { runs: number; forbidden_evidence_retrieved_count: number }
>;
const abQuality = ab.quality_validity as {
  quality_metrics_valid: boolean;
  voided_metrics: string[];
};
const providerLabel = ab.provider === "cohere" ? "Cohere" : ab.provider;
const abRunDistribution = abBuilds
  .map((build) => `${abByBuild[build]?.runs ?? 0} ${build}`)
  .join(" + ");

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
    label: "Security-matrix deterministic Replays passed",
    value: `${integrity.security_matrix_pass_count} / ${integrity.security_matrix_declared_count}`,
    note: `${integrity.security_matrix_full_replay_execution_count}/${integrity.security_matrix_declared_count} executed · ${integrity.security_matrix_failure_count} open issues`,
  },
  {
    label: "Stored attack payload controls",
    value: `${integrity.attack_payload_control_pass_count} / ${integrity.attack_payload_control_execution_count}`,
    note: "deterministic detector executions, not full Replays",
  },
  {
    label: `Retained live ${providerLabel} A/B`,
    value: `${ab.run_count} runs`,
    note: abRunDistribution,
  },
  {
    label: "Live A/B quality validity",
    value: abQuality.quality_metrics_valid ? "VALID" : "VOID",
    note: abQuality.quality_metrics_valid
      ? "quality metrics passed the publication validity gate"
      : `${abQuality.voided_metrics.join(", ")} are not evidence`,
  },
];

export default function ResultsPage() {
  return (
    <main className="pageShell" id="main-content">
      <header className="pageIntro">
        <p className="eyebrow">RELEASE SCORECARD</p>
        <h1>Evidence before verdict.</h1>
        <p>
          This scorecard separates deterministic development-fixture outcomes
          from a retained live-provider A/B. No held-out, human-review, cost, or
          final-release result exists.
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
      <section className="panel" aria-labelledby="ab-run">
        <h2 id="ab-run">Measured guarded vs unguarded A/B</h2>
        <p>
          A retained live {providerLabel} A/B contains {ab.run_count} runs:{" "}
          {ab.scenario_count} scenarios across {ab.repetitions} repetitions and
          both builds ({abRunDistribution}). Its pre-retrieval authorization
          evidence is valid: forbidden evidence reached retrieval in{" "}
          {abByBuild["unsafe-v0"]?.forbidden_evidence_retrieved_count ?? 0}/
          {abByBuild["unsafe-v0"]?.runs ?? 0} unsafe runs and{" "}
          {abByBuild["guarded-v1"]?.forbidden_evidence_retrieved_count ?? 0}/
          {abByBuild["guarded-v1"]?.runs ?? 0} guarded runs. The snapshot marks
          its model-dependent quality metrics <strong>VOID</strong>; they are
          not promoted as Cohere quality claims.
        </p>
        <p>
          <Link href="/results/ab/">Read the measured A/B results</Link>
        </p>
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
          <strong>
            {abQuality.quality_metrics_valid
              ? "valid in retained live A/B"
              : "VOID in retained live A/B"}
          </strong>
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
      <section className="panel" aria-labelledby="matrix-failures">
        <h2 id="matrix-failures">Security-matrix open issues</h2>
        <p>
          Every declared cell remains in the checksummed scorecard snapshot,
          including failures. This is a recorded deterministic
          application-control suite, not a live-model attack suite.
        </p>
        {integrity.security_matrix_failure_count === 0 ? (
          <p className="fallbackNotice">
            0 open issues in this execution. All{" "}
            {integrity.security_matrix_full_replay_execution_count} declared
            cells executed and passed the recorded-fixture controls.
          </p>
        ) : (
          <ol>
            {integrity.security_matrix_results
              .filter((cell) => !cell.passed)
              .map((cell) => (
                <li key={cell.scenario_id}>
                  <b>{cell.scenario_id}</b>: {cell.failure_reasons.join(", ")}
                </li>
              ))}
          </ol>
        )}
        <p>
          The matrix still uses one stored hostile artifact across its declared
          family/variant labels, and its draft truth IDs are not independent
          semantic truths. The release verdict remains NO SHIP.
        </p>
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
