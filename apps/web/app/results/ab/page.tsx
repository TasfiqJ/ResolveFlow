import Link from "next/link";
import ab from "../../../public/snapshots/ab-site-current.json";

const BUILDS = ab.builds as string[];

type BuildAggregate = {
  runs: number;
  forbidden_evidence_exposure_count: number;
  forbidden_evidence_retrieved_count: number;
  citation_precision_mean: number | null;
  runs_with_citations: number;
  route_accuracy: number;
  route_correct_count: number;
  completion_rate: number;
  needs_review_count: number;
  successful_forbidden_effect_runs: number;
  attempted_forbidden_effect_total: number;
  external_write_total: number;
  attacks_delivered_to_model: number;
  attacks_not_exercised: number;
  wall_clock_ms: Record<string, number> | null;
  provider_call_ms: Record<string, number> | null;
  stage_ms_median: Record<string, number>;
  stage_ms: Record<string, Record<string, number>>;
  stage_attribution: {
    runs: number;
    attributed_fraction_p50: number;
    attributed_fraction_min: number;
    unattributed_ms_p50: number;
    unattributed_ms_max: number;
  } | null;
};

type FamilyOutcome = {
  variants: number;
  variants_delivered_to_model: number;
  variants_not_exercised: string[];
  got_through: string[];
  detector_fired: string[];
  detector_silent: string[];
};

const byBuild = ab.by_build as Record<string, BuildAggregate>;
const timing = (ab as { timing?: { clock?: string; clock_resolution_ns?: number; platform?: string } }).timing ?? {};
const families = ab.attack_family_outcomes as Record<string, FamilyOutcome>;
const openIssues = ab.open_issues as string[];

const pct = (value: number | null) =>
  value === null || value === undefined
    ? "not measured"
    : `${(value * 100).toFixed(1)}%`;
const num = (value: number | null | undefined) =>
  value === null || value === undefined ? "not measured" : String(value);

const METRIC_ROWS: Array<{
  label: string;
  key: keyof BuildAggregate;
  kind: "count" | "pct";
}> = [
  { label: "Runs", key: "runs", kind: "count" },
  {
    label: "Forbidden-evidence exposure (cited)",
    key: "forbidden_evidence_exposure_count",
    kind: "count",
  },
  {
    label: "Forbidden evidence reached retrieval",
    key: "forbidden_evidence_retrieved_count",
    kind: "count",
  },
  {
    label: "Citation precision (mean)",
    key: "citation_precision_mean",
    kind: "count",
  },
  {
    label: "Runs producing any citation",
    key: "runs_with_citations",
    kind: "count",
  },
  { label: "Route accuracy", key: "route_accuracy", kind: "pct" },
  { label: "Completion rate", key: "completion_rate", kind: "pct" },
  {
    label: "Runs marked needs_review",
    key: "needs_review_count",
    kind: "count",
  },
  {
    label: "Runs with a successful forbidden effect",
    key: "successful_forbidden_effect_runs",
    kind: "count",
  },
  {
    label: "Forbidden-effect attempts detected",
    key: "attempted_forbidden_effect_total",
    kind: "count",
  },
  { label: "External writes", key: "external_write_total", kind: "count" },
  {
    label: "Attacks delivered to the model",
    key: "attacks_delivered_to_model",
    kind: "count",
  },
  {
    label: "Attacks never exercised",
    key: "attacks_not_exercised",
    kind: "count",
  },
];

const STAGES = Array.from(
  new Set(
    BUILDS.flatMap((build) =>
      Object.keys(byBuild[build]?.stage_ms ?? {}),
    ),
  ),
).sort();

export default function AbResultsPage() {
  return (
    <main className="pageShell" id="main-content">
      <header className="pageIntro">
        <p className="eyebrow">MEASURED A/B</p>
        <h1>Guarded vs unguarded, {ab.run_count} runs.</h1>
        <p>
          Every number on this page was read out of{" "}
          <code>eval/results/ab-summary-{ab.provider}.json</code>, produced by
          an execution of the harness. Nothing here is projected, expected, or
          illustrative. Where something was not measured, this page says so.
        </p>
      </header>

      <section className="pageSection">
        <h2>Read this before any number</h2>
        <p>
          <strong>{ab.provider_caveat}</strong>
        </p>
      </section>

      <section className="pageSection">
        <h2>An earlier published run was voided</h2>
        <p>
          <strong>
            A live Cohere A/B was previously published from this repository and
            is VOID.
          </strong>{" "}
          Its agent token ceiling was the default 4,096 total tokens, sized for
          an earlier five-document corpus. Against the twenty-document corpus an
          evidence-pass prompt runs to roughly 3.3k&ndash;5.1k input tokens, and
          the ceiling counts input plus output, so all 32 of its runs terminated
          with <code>token_budget_exhausted</code> before any model output was
          parsed. Citation precision, route accuracy, completion rate and every
          attack outcome in that run were artifacts of a harness
          misconfiguration and carried no information about model or control
          behaviour.
        </p>
        <p>
          Two changes were made in response and both are exercised by the run on
          this page: the evaluation token ceiling is now 32,768, and
          <code> assert_budget_fits_corpus</code> refuses to start a run whose
          ceiling cannot fit the corpus, before a single provider call is spent.
          Zero runs on this page terminated with{" "}
          <code>token_budget_exhausted</code>.
        </p>
        <p>
          <strong>
            No live Cohere run has been performed since that fix.
          </strong>{" "}
          The fix is verified against the fixture provider only. Until a live
          run is published, this project makes no measured claim about model
          citation behaviour, model routing, model robustness to any attack
          family, real provider latency, or real token consumption.
        </p>
      </section>

      <section className="pageSection">
        <h2>Provenance</h2>
        <ul>
          <li>
            Results hash: <code>{ab.results_hash}</code>
          </li>
          <li>
            Commit: <code>{ab.commit}</code>
          </li>
          <li>Generated at: {ab.generated_at}</li>
          <li>
            Scenarios: {ab.scenario_count} (8 benign, 8 attack) · Builds:{" "}
            {BUILDS.join(", ")}
          </li>
          <li>
            Provider calls consumed:{" "}
            <strong>
              {ab.budget
                ? (ab.budget as { total_calls: number }).total_calls
                : 0}
            </strong>
          </li>
        </ul>
      </section>

      <section className="pageSection">
        <h2>Results</h2>
        <table>
          <thead>
            <tr>
              <th scope="col">Metric</th>
              {BUILDS.map((build) => (
                <th key={build} scope="col">
                  {build}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {METRIC_ROWS.map((row) => (
              <tr key={row.label}>
                <th scope="row">{row.label}</th>
                {BUILDS.map((build) => {
                  const value = byBuild[build]?.[row.key] as number | null;
                  return (
                    <td key={build}>
                      {row.kind === "pct" ? pct(value) : num(value)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="pageSection">
        <h2>Latency</h2>
        <p>
          End-to-end wall time and provider-call time are separate claims and
          are never added together. Measured on one machine in one pass; no
          figure here is a service level objective.
        </p>
        <table>
          <thead>
            <tr>
              <th scope="col">Build</th>
              <th scope="col">Wall median (ms)</th>
              <th scope="col">Wall p95 (ms)</th>
              <th scope="col">Provider median (ms)</th>
            </tr>
          </thead>
          <tbody>
            {BUILDS.map((build) => (
              <tr key={build}>
                <th scope="row">{build}</th>
                <td>{num(byBuild[build]?.wall_clock_ms?.median ?? null)}</td>
                <td>{num(byBuild[build]?.wall_clock_ms?.p95 ?? null)}</td>
                <td>{num(byBuild[build]?.provider_call_ms?.median ?? null)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <h3>Per-stage latency, p50 and p95 (ms)</h3>
        <p>
          Clock: <code>{timing.clock ?? "unrecorded"}</code>, advertised
          resolution {timing.clock_resolution_ns ?? "unrecorded"} ns, on{" "}
          {timing.platform ?? "unrecorded"}. An earlier run reported 0.0 ms for
          eleven stages, every value a multiple of 15.625 ms &mdash; the Windows{" "}
          <code>time.monotonic</code> tick. Those readings meant the clock could
          not resolve the stage, not that the stage was free. Stage spans are
          not a partition of the run, so these do not sum to wall time.
        </p>
        <table>
          <thead>
            <tr>
              <th scope="col">Stage</th>
              {BUILDS.map((build) => (
                <th key={build} scope="col" colSpan={2}>
                  {build}
                </th>
              ))}
            </tr>
            <tr>
              <th scope="col" />
              {BUILDS.map((build) => [
                <th key={`${build}-p50`} scope="col">
                  p50
                </th>,
                <th key={`${build}-p95`} scope="col">
                  p95
                </th>,
              ])}
            </tr>
          </thead>
          <tbody>
            {STAGES.map((stage) => (
              <tr key={stage}>
                <th scope="row">
                  <code>{stage}</code>
                </th>
                {BUILDS.map((build) => [
                  <td key={`${build}-p50`}>
                    {num(byBuild[build]?.stage_ms?.[stage]?.p50 ?? null)}
                  </td>,
                  <td key={`${build}-p95`}>
                    {num(byBuild[build]?.stage_ms?.[stage]?.p95 ?? null)}
                  </td>,
                ])}
              </tr>
            ))}
          </tbody>
        </table>
        <h3>Unattributed wall time</h3>
        <table>
          <thead>
            <tr>
              <th scope="col">Build</th>
              <th scope="col">Wall time inside a named stage (p50)</th>
              <th scope="col">Unattributed ms (p50)</th>
            </tr>
          </thead>
          <tbody>
            {BUILDS.map((build) => (
              <tr key={build}>
                <th scope="row">{build}</th>
                <td>
                  {pct(
                    byBuild[build]?.stage_attribution
                      ?.attributed_fraction_p50 ?? null,
                  )}
                </td>
                <td>
                  {num(
                    byBuild[build]?.stage_attribution?.unattributed_ms_p50 ??
                      null,
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="pageSection">
        <h2>Attack families</h2>
        <p>
          Four families, two variants each, eight independent artifacts.
          Variants differ in mechanism, not wording. A variant that never
          reached the candidate set was never tested and is reported as such
          rather than counted as a pass.
        </p>
        <table>
          <thead>
            <tr>
              <th scope="col">Family / build</th>
              <th scope="col">Delivered</th>
              <th scope="col">Never exercised</th>
              <th scope="col">Got through</th>
              <th scope="col">Detector silent</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(families)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([key, value]) => (
                <tr key={key}>
                  <th scope="row">
                    <code>{key}</code>
                  </th>
                  <td>
                    {value.variants_delivered_to_model}/{value.variants}
                  </td>
                  <td>{value.variants_not_exercised.join(", ") || "none"}</td>
                  <td>{value.got_through.join(", ") || "none"}</td>
                  <td>{value.detector_silent.join(", ") || "none"}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </section>

      <section className="pageSection">
        <h2>Open issues</h2>
        <p>
          These are published because they were found, not because they are
          comfortable. Nothing was tuned to remove them.
        </p>
        <ul>
          {openIssues.map((issue) => (
            <li key={issue}>{issue}</li>
          ))}
        </ul>
      </section>

      <section className="pageSection">
        <h2>What remains unvalidated</h2>
        <ul>
          <li>
            The corpus, tenants, incidents, and attacks are synthetic and
            agent-authored. No human has reviewed them for realism or coverage.
          </li>
          <li>
            Each attack variant is a single scenario against a single query. One
            trial is not a resistance rate. No confidence interval is claimed.
          </li>
          <li>
            Absence of a successful attack is evidence about these eight
            mechanisms only, and says nothing about mechanisms not in the
            catalog.
          </li>
          <li>
            No live provider run has been executed since the token-budget fix,
            so nothing on this page is evidence about Cohere models. Every
            model-dependent number here is a property of the deterministic
            fixture stub.
          </li>
          <li>
            One repetition per cell. No variance across repeated trials was
            measured, so no number here has a confidence interval and no
            difference between the two builds is claimed to be significant.
          </li>
          <li>
            Attack payloads were authored before the guarded build existed. No
            adaptive attack &mdash; one written with knowledge of these defences
            &mdash; has been attempted, so &ldquo;nothing got through&rdquo;
            describes this fixed payload set and not an attacker who adapts.
          </li>
          <li>
            No held-out split, no human review, no cost result, and no
            final-release verdict exists. <strong>NO SHIP.</strong>
          </li>
        </ul>
      </section>

      <section className="pageSection">
        <h2>Raw artifacts</h2>
        <ul>
          <li>
            <a href="./ab-site-current.json">ab-site-current.json</a> (this
            page&rsquo;s source) and its{" "}
            <a href="./ab-site-current.json.sha256">SHA-256</a>
          </li>
          <li>
            In the repository:{" "}
            <code>eval/results/ab-summary-{ab.provider}.json</code>, the per-run
            snapshots under <code>eval/results/runs/</code>,{" "}
            <code>eval/results/README.md</code>,{" "}
            <code>eval/results/results-table-{ab.provider}.md</code>, and{" "}
            <code>eval/results/SHA256SUMS-{ab.provider}.md</code>
          </li>
        </ul>
        <p>
          <Link href="/results/">Back to the release scorecard</Link>
        </p>
      </section>
    </main>
  );
}
