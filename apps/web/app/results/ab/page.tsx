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
  terminal_reasons: Record<string, number>;
};

type QualityValidity = {
  quality_metrics_valid: boolean;
  void_reasons: string[];
  voided_metrics: string[];
};

type ProviderTelemetryValidity = {
  valid: boolean;
  status: string;
  reason_codes: string[];
  retained_snapshot_observations: {
    matched_chat_trace_count: number;
  };
  ledger_observations: {
    record_count: number;
    chat_record_count: number;
    rerank_record_count: number;
    dry_pass_record_count: number;
    published_run_record_count: number;
    reported_total_calls: number;
    reported_search_units: number | null;
    search_unit_accounting: string;
  };
};

type RecoveryReceipt = {
  complete_trials_used: number[];
  excluded_snapshot_count: number;
  excluded_snapshot_directory: string;
  note: string;
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
const timing =
  (
    ab as {
      timing?: {
        clock?: string;
        clock_resolution_ns?: number;
        platform?: string;
      };
    }
  ).timing ?? {};
const families = ab.attack_family_outcomes as Record<string, FamilyOutcome>;
const openIssues = ab.open_issues as string[];
const qualityValidity = ab.quality_validity as QualityValidity;
const providerLabel = ab.provider === "cohere" ? "Cohere" : ab.provider;
const providerTelemetry =
  ab.provider_telemetry_validity as ProviderTelemetryValidity;
const ledger = providerTelemetry.ledger_observations;
const recovery = ab.recovered_from_snapshots as RecoveryReceipt;
const runDistribution = BUILDS.map(
  (build) => `${byBuild[build]?.runs ?? 0} ${build}`,
).join(" + ");
const currentTokenBudgetExhaustions = BUILDS.reduce(
  (total, build) =>
    total + (byBuild[build]?.terminal_reasons?.token_budget_exhausted ?? 0),
  0,
);
const familyCount = new Set(
  Object.keys(families).map((key) => key.split("/")[0]),
).size;

const pct = (value: number | null) =>
  value === null || value === undefined
    ? "not measured"
    : `${(value * 100).toFixed(1)}%`;
const num = (value: number | null | undefined) =>
  value === null || value === undefined ? "not measured" : String(value);
const variantIds = (values: string[]) =>
  Array.from(new Set(values)).join(", ") || "none";

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
    kind: "pct",
  },
  {
    label: "Runs producing any citation",
    key: "runs_with_citations",
    kind: "count",
  },
  {
    label: "Route accuracy",
    key: "route_accuracy",
    kind: "pct",
  },
  {
    label: "Completion rate",
    key: "completion_rate",
    kind: "pct",
  },
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
    BUILDS.flatMap((build) => Object.keys(byBuild[build]?.stage_ms ?? {})),
  ),
).sort();

export default function AbResultsPage() {
  return (
    <main className="pageShell" id="main-content">
      <header className="pageIntro">
        <p className="eyebrow">MEASURED A/B</p>
        <h1>
          Live {providerLabel}, guarded vs unguarded, {ab.run_count} runs.
        </h1>
        <p>
          Every current-run metric on this page was read out of{" "}
          <code>eval/results/ab-summary-{ab.provider}.json</code>, produced by
          an execution of the harness. Nothing here is projected, expected, or
          illustrative. The separately labeled earlier-run history comes from
          its retained publication record. Where something was not measured,
          this page says so.
        </p>
      </header>

      <section className="pageSection">
        <h2>Read this before any number</h2>
        <p>
          <strong>{ab.provider_caveat}</strong>
        </p>
        <p>
          This retained execution contains {runDistribution}. Its pre-retrieval
          authorization evidence is valid: forbidden evidence reached retrieval
          in {byBuild["unsafe-v0"]?.forbidden_evidence_retrieved_count ?? 0}/
          {byBuild["unsafe-v0"]?.runs ?? 0} unsafe runs and{" "}
          {byBuild["guarded-v1"]?.forbidden_evidence_retrieved_count ?? 0}/
          {byBuild["guarded-v1"]?.runs ?? 0} guarded runs. This measures the
          application authorization boundary before any model call; it is not a
          claim about model safety.
        </p>
        <p className="fallbackNotice">
          Quality validity:{" "}
          <strong>
            {qualityValidity.quality_metrics_valid ? "VALID" : "VOID"}
          </strong>
          . {qualityValidity.void_reasons.join("; ")}. The raw quality values
          remain visible for audit, but are not results.
        </p>
      </section>

      <section className="pageSection recoveryNote">
        <p className="eyebrow">COHORT INTEGRITY</p>
        <h2>
          One coherent invocation, recovered without another provider call.
        </h2>
        <p>
          This publication uses the {ab.run_count} snapshots from complete trial{" "}
          {recovery.complete_trials_used.join(", ")} only.{" "}
          {recovery.excluded_snapshot_count} snapshots from other invocation
          timestamps carried a different execution identity, so they were
          quarantined under <code>{recovery.excluded_snapshot_directory}</code>{" "}
          instead of being blended into the result.
        </p>
        <p>
          <strong>Provider telemetry: {providerTelemetry.status}.</strong>{" "}
          {providerTelemetry.valid ? (
            <>
              {
                providerTelemetry.retained_snapshot_observations
                  .matched_chat_trace_count
              }{" "}
              selected Chat traces bind by response-ID fingerprint; 32 Rerank
              calls reconcile by exact scenario/build/model cardinality; the
              other {ledger.dry_pass_record_count} records map to the required
              four-run dry pass. Recovery spent zero provider calls.
            </>
          ) : (
            <>
              Aggregate provider-usage claims are VOID because the ledger did
              not reconcile.
            </>
          )}
          {providerTelemetry.valid &&
            (ledger.search_unit_accounting === "legacy_unavailable" ? (
              <>
                {" "}
                This historical ledger predates Rerank search-unit capture; that
                usage is unavailable, not zero.
              </>
            ) : (
              <>
                {" "}
                Recorded Rerank usage: {ledger.reported_search_units} search
                units.
              </>
            ))}
        </p>
      </section>

      <section className="pageSection">
        <h2>An earlier published run was voided</h2>
        <p>
          <strong>
            A live Cohere A/B was previously published from this repository and
            is VOID.
          </strong>{" "}
          Its observed-usage stop threshold was the default 4,096 tokens, sized
          for an earlier five-document corpus. Against the twenty-document
          corpus an evidence-pass prompt runs to roughly 3.3k&ndash;5.1k input
          tokens. Provider-reported input plus output crossed the threshold
          after the first response, so all 32 runs terminated with{" "}
          <code>token_budget_exhausted</code> before model output was parsed.
          Citation precision, route accuracy, completion rate and every attack
          outcome in that run were artifacts of a harness misconfiguration and
          carried no information about model or control behaviour.
        </p>
        <p>
          Two changes were made in response and both are present in the run on
          this page: the observed-usage stop threshold is 32,768, and
          <code> assert_budget_fits_corpus</code> refuses to start a run whose
          ceiling cannot fit the corpus, before a single provider call is spent.
          The retained run still records {currentTokenBudgetExhaustions}{" "}
          <code>token_budget_exhausted</code> terminal outcomes; the preflight
          guards corpus fit, not every possible multi-round execution path.
        </p>
        <p>
          <strong>
            A live {providerLabel} A/B was performed after that fix and is the{" "}
            {ab.run_count}-run artifact shown here.
          </strong>{" "}
          Its reconciled invocation ledger contains{" "}
          {ledger.reported_total_calls} calls: {ledger.dry_pass_record_count} in
          the required dry pass and {ledger.published_run_record_count} in the
          published full pass. Low completion means it does not support claims
          about model citation quality, routing quality, or broad attack
          robustness; those quality metrics are explicitly void.
        </p>
      </section>

      <section className="pageSection">
        <h2>Provenance</h2>
        <ul>
          <li>
            Results hash: <code>{ab.results_hash}</code>
          </li>
          <li>
            Execution git state: <code>{ab.execution_commit}</code>; the exact
            dirty diff was not retained
          </li>
          <li>
            Publication base commit: <code>{ab.publication_base_commit}</code>{" "}
            (not the execution commit)
          </li>
          <li>Generated at: {ab.generated_at}</li>
          <li>
            Scenarios: {ab.scenario_count} (8 benign, 8 attack) · Builds:{" "}
            {BUILDS.join(", ")}
          </li>
          <li>Runs by build: {runDistribution}</li>
          <li>
            Quality metrics:{" "}
            <strong>
              {qualityValidity.quality_metrics_valid ? "VALID" : "VOID"}
            </strong>
          </li>
          <li>
            Reconciled invocation calls:{" "}
            <strong>{ledger.reported_total_calls}</strong>, including the dry
            pass
          </li>
        </ul>
      </section>

      <section className="pageSection">
        <h2>Results</h2>
        <div className="tableWrap">
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
                    const formatted =
                      row.kind === "pct" ? pct(value) : num(value);
                    const isVoidedQualityMetric =
                      qualityValidity.voided_metrics.includes(String(row.key));
                    return (
                      <td key={build}>
                        {isVoidedQualityMetric &&
                        !qualityValidity.quality_metrics_valid
                          ? `VOID · raw ${formatted}`
                          : formatted}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="pageSection">
        <h2>Latency</h2>
        <p>
          End-to-end wall time and recorded Chat-trace time are separate claims
          and are never added together. Rerank appears in the stage table.
          Measured on one machine during one retained invocation; no figure here
          is a service level objective.
        </p>
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Build</th>
                <th scope="col">Wall median (ms)</th>
                <th scope="col">Wall p95 (ms)</th>
                <th scope="col">Recorded Chat-trace median (ms)</th>
              </tr>
            </thead>
            <tbody>
              {BUILDS.map((build) => (
                <tr key={build}>
                  <th scope="row">{build}</th>
                  <td>{num(byBuild[build]?.wall_clock_ms?.median ?? null)}</td>
                  <td>{num(byBuild[build]?.wall_clock_ms?.p95 ?? null)}</td>
                  <td>
                    {num(byBuild[build]?.provider_call_ms?.median ?? null)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
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
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th scope="col" rowSpan={2}>
                  Stage
                </th>
                {BUILDS.map((build) => (
                  <th key={build} scope="col" colSpan={2}>
                    {build}
                  </th>
                ))}
              </tr>
              <tr>
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
        </div>
        <h3>Unattributed wall time</h3>
        <div className="tableWrap">
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
        </div>
      </section>

      <section className="pageSection">
        <h2>Attack families</h2>
        <p>
          {familyCount} families, two authored variants per family, replayed
          across {ab.repetitions} repetitions ({2 * ab.repetitions} trials per
          family and build). Variants differ in mechanism, not wording. A
          variant that never reached the candidate set was never tested and is
          reported as such rather than counted as a pass.
        </p>
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Family / build</th>
                <th scope="col">Delivered trials</th>
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
                    <td>{variantIds(value.variants_not_exercised)}</td>
                    <td>{variantIds(value.got_through)}</td>
                    <td>{variantIds(value.detector_silent)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
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
            Each authored attack variant is one scenario against one query,
            replayed {ab.repetitions} times. That remains too narrow to be a
            general resistance rate.
          </li>
          <li>
            Absence of a successful attack is evidence about these eight
            mechanisms only, and says nothing about mechanisms not in the
            catalog.
          </li>
          <li>
            This is a live {providerLabel} run, but the snapshot marks its
            model-dependent quality metrics{" "}
            <strong>
              {qualityValidity.quality_metrics_valid ? "VALID" : "VOID"}
            </strong>
            . The valid pre-retrieval authorization result is an application
            control result, not evidence of model safety.
          </li>
          <li>
            {ab.repetitions} repetition was recorded per build/scenario cell.
            The snapshot includes descriptive, execution-level Wilson intervals
            for binary outcomes, but the authored set is not a random population
            sample and does not justify an inferential, broad-significance, or
            production-readiness claim.
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
            <Link href="/snapshots/ab-site-current.json">
              ab-site-current.json
            </Link>{" "}
            (this page&rsquo;s source) and its{" "}
            <Link href="/snapshots/ab-site-current.json.sha256">SHA-256</Link>
          </li>
          <li>
            In the repository:{" "}
            <code>eval/results/ab-summary-{ab.provider}.json</code>, the per-run
            canonical snapshots under <code>eval/results/runs/cohere/</code>,{" "}
            the excluded prior invocation under{" "}
            <code>{recovery.excluded_snapshot_directory}</code>,{" "}
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
