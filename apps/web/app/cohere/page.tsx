import type { Metadata } from "next";
import Link from "next/link";
import ab from "../../public/snapshots/ab-site-current.json";
import live from "../../public/snapshots/hero-cohere-live.json";

export const metadata: Metadata = {
  title: "Cohere integration receipt — ResolveFlow",
  description:
    "A recorded, source-linked view of how ResolveFlow uses Command A+, Embed v4, Rerank v4, strict tools, citations, and structured output.",
};

const guarded = ab.by_build["guarded-v1"];
const unsafe = ab.by_build["unsafe-v0"];
const providerCalls = live.provider_traces.length;
const toolCalls = live.tool_traces;

const pipeline = [
  {
    number: "01 · ORDINARY CODE",
    title: "Authorize first",
    body: `${live.retrieval.eligible_chunk_count} eligible synthetic chunks were materialized before any model ranking. Tenant, role, region, freshness, and version remain application controls.`,
    owner: "application",
  },
  {
    number: "02 · EMBED V4",
    title: "Find semantic candidates",
    body: `${live.retrieval.embedding_model} supplied the semantic leg of hybrid retrieval over the already-authorized snapshot. The synthetic query and retained vector cache are checksummed in the repository; the static page omits raw vectors for readability.`,
    owner: "cohere",
  },
  {
    number: "03 · RERANK V4",
    title: "Reorder the shortlist",
    body: `${live.retrieval.rerank_model} reranked ${live.retrieval.candidates.length} fused candidates. Every position, relevance score, payload checksum, and model ID is retained.`,
    owner: "cohere",
  },
  {
    number: "04 · COMMAND A+",
    title: "Use bounded tools",
    body: `${providerCalls} recorded Chat calls used ${live.provider_traces[0].model}, strict schemas, and four allowlisted tools. One unauthorized lookup was denied by ordinary code.`,
    owner: "cohere",
  },
  {
    number: "05 · VERIFIED GRAPH",
    title: "Close every claim",
    body: "The second pass receives verified IDs, not original documents or tools. Its live malformed selection failed closed; the current contract additionally binds allowed IDs into Cohere's JSON Schema.",
    owner: "application",
  },
  {
    number: "06 · RELEASE GATE",
    title: "Stop safely",
    body: `The retained run ended ${live.response.disposition}: route unresolved, ${live.response.unknowns.length} explicit unknowns, Jira not proposed, and zero external writes.`,
    owner: "application",
  },
] as const;

export default function CoherePage() {
  return (
    <main className="pageShell" id="main-content">
      <section className="cohereHero">
        <header className="pageIntro">
          <p className="eyebrow">COHERE INTEGRATION RECEIPT</p>
          <h1>Cohere is the engine. Ordinary code is the safety boundary.</h1>
          <p>
            This is a recorded, inspectable execution—not a mock dashboard and
            not a public inference endpoint. It shows where Command A+, Embed
            v4, Rerank v4, strict tools, verified citations, and structured
            output fit inside a fail-closed release gate.
          </p>
        </header>
        <aside className="cohereReceipt" aria-label="Recorded live run receipt">
          <span>RECORDED LIVE-PROVIDER RUN</span>
          <strong>{live.response.disposition.replace("_", " ")}</strong>
          <p className="cohereFinePrint">
            Synthetic HelioPay incident · {live.generated_at.slice(0, 10)} · no
            Slack or Jira write
          </p>
          <dl>
            <dt>Command calls</dt>
            <dd>{providerCalls}</dd>
            <dt>Tool calls</dt>
            <dd>{toolCalls.length}</dd>
            <dt>Retrieved candidates</dt>
            <dd>{live.retrieval.candidates.length}</dd>
            <dt>Verified citations</dt>
            <dd>{live.response.citations.length}</dd>
            <dt>External writes</dt>
            <dd>0</dd>
          </dl>
        </aside>
      </section>

      <section aria-labelledby="pipeline-title">
        <p className="eyebrow">ONE SHARED RESOLVE / REPLAY PATH</p>
        <h2 id="pipeline-title">The execution, boundary by boundary</h2>
        <div className="coherePipeline">
          {pipeline.map((step) => (
            <article
              className={`cohereBoundary ${step.owner}`}
              key={step.number}
            >
              <small>{step.number}</small>
              <h2>{step.title}</h2>
              <p>{step.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="twoColumn" aria-label="Responsibility split">
        <article className="panel cohereBoundary">
          <span className="boundaryLabel">COHERE OWNS</span>
          <h2>Model capability</h2>
          <ul>
            <li>Embed v4 semantic vectors with explicit input types.</li>
            <li>Rerank v4 relevance over a fixed authorized candidate set.</li>
            <li>Command A+ tool selection and evidence-linked synthesis.</li>
            <li>Strict tool arguments and JSON Schema-constrained output.</li>
            <li>Fine-grained citation spans and source identifiers.</li>
          </ul>
        </article>
        <article className="panel cohereBoundary application">
          <span className="boundaryLabel">RESOLVEFLOW OWNS</span>
          <h2>Authority and effects</h2>
          <ul>
            <li>
              Guarded-v1 applies ACL filtering before Embed or Rerank sees a
              candidate.
            </li>
            <li>
              Typed tool registry, argument checks, timeouts, and budgets.
            </li>
            <li>Exact evidence graph, freshness, and source-closure checks.</li>
            <li>
              Graph-bound ID allowlists plus deterministic final rendering.
            </li>
            <li>
              Exact payload approval before any connector can write, assuming
              caller identity was authenticated by a trusted upstream service.
            </li>
          </ul>
        </article>
      </section>

      <section className="panel" aria-labelledby="tool-receipt-title">
        <span className="boundaryLabel">RECORDED COMMAND A+ TOOL TRACE</span>
        <h2 id="tool-receipt-title">A useful denial is part of the answer</h2>
        <p>
          The model may request a tool; it cannot grant itself authority. The
          rejected lookup becomes an explicit unknown instead of disappearing
          behind a fluent answer.
        </p>
        <div className="cohereTableWrap">
          <table className="cohereTable">
            <thead>
              <tr>
                <th scope="col">Tool</th>
                <th scope="col">Authorization</th>
                <th scope="col">Outcome</th>
                <th scope="col">Recorded provenance</th>
                <th scope="col">External write</th>
              </tr>
            </thead>
            <tbody>
              {toolCalls.map((call) => (
                <tr key={call.tool_call_id}>
                  <td>
                    <code>{call.name}</code>
                  </td>
                  <td>
                    <span
                      className={`cohereStatus ${
                        call.authorization === "denied" ? "denied" : ""
                      }`}
                    >
                      {call.authorization}
                    </span>
                  </td>
                  <td>{call.safe_error_code ?? call.status}</td>
                  <td>{call.provenance_ids.join(", ") || "none"}</td>
                  <td>{call.external_write ? "yes" : "no"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="metricGrid" aria-label="Retained Cohere A/B receipt">
        <article>
          <small>LIVE A/B RUNS</small>
          <strong>{ab.run_count}</strong>
          <p>
            {ab.provider} · {ab.builds.length} builds · synthetic corpus
          </p>
        </article>
        <article>
          <small>FORBIDDEN RETRIEVAL · UNSAFE</small>
          <strong>
            {unsafe.forbidden_evidence_retrieved_count}/{unsafe.runs}
          </strong>
          <p>The intentionally unsafe Replay build admitted the artifact.</p>
        </article>
        <article>
          <small>FORBIDDEN RETRIEVAL · GUARDED</small>
          <strong>
            {guarded.forbidden_evidence_retrieved_count}/{guarded.runs}
          </strong>
          <p>
            The guarded application boundary refused it before model retrieval.
          </p>
        </article>
      </section>

      <section className="panel recoveryNote">
        <span className="boundaryLabel">COHORT RECEIPT</span>
        <h2>One invocation in; mixed history out</h2>
        <p>
          The current A/B projection keeps one coherent {ab.run_count}-snapshot
          invocation. It excludes{" "}
          {ab.recovered_from_snapshots.excluded_snapshot_count} older snapshots
          with a different execution timestamp and identity. The retained{" "}
          {ab.provider_telemetry_validity.ledger_observations.record_count}
          -record ledger reconciles to the four-run dry pass and selected full
          pass; offline recovery spent zero provider calls. This historical
          ledger predates Rerank search-unit capture, so that usage is
          unavailable rather than reported as zero.
        </p>
      </section>

      <section className="twoColumn">
        <article className="panel">
          <span className="boundaryLabel">VALID RESULT</span>
          <h2>{`Authorization moved ${unsafe.forbidden_evidence_retrieved_count}/${unsafe.runs} to ${guarded.forbidden_evidence_retrieved_count}/${guarded.runs}`}</h2>
          <p>
            That comparison is pre-model and mechanically measured. The retained
            artifact reports a guarded-minus-unsafe difference of −100
            percentage points, with a descriptive execution-level interval and
            checksums published. The authored scenarios are not a random
            population sample.
          </p>
        </article>
        <article className="panel">
          <span className="boundaryLabel">VOID QUALITY METRICS</span>
          <h2>No model-quality victory is claimed</h2>
          <p>
            Completion was too low for representative citation, routing, or
            completion claims. The failure is retained, and this hardening pass
            makes no post-change live result because no additional provider run
            was performed.
          </p>
        </article>
      </section>

      <section className="panel">
        <span className="boundaryLabel">AFTER THE RETAINED RUN</span>
        <h2>Six Cohere contract boundaries, verified offline</h2>
        <ul>
          <li>
            Visible-text citations retain their content index, type, exact span,
            and nested source IDs; mismatched or hidden-content spans are
            rejected.
          </li>
          <li>
            Evidence calls request accurate citations and bounded tool use; the
            last evidence slot can force <code>tool_choice=NONE</code>, while
            the final structure pass carries no tools.
          </li>
          <li>
            The structure schema binds the exact graph hash and field-specific
            verified IDs with Cohere-supported <code>const</code> and{" "}
            <code>enum</code> constraints; local validation still fails closed.
          </li>
          <li>
            Tool-result messages validate against Cohere SDK 7 shapes, bind
            requested record identities plus canonical source data to checksums
            and provenance, and support facts only from the exact cited
            allowlisted quote.
          </li>
          <li>
            Rerank fixes the document-token ceiling, confirms the active model,
            and rejects missing results, duplicate/out-of-range indexes, and
            non-finite scores.
          </li>
          <li>
            Native request timeouts disable hidden SDK retries; the counted
            retry/throttle layer shares the remaining cooperative deadline and
            rechecks it after return. This does not claim hard provider-side
            cancellation. Malformed provider shapes become safe, typed failures.
          </li>
        </ul>
        <p className="cohereFinePrint">
          These are code-and-contract improvements, not a retroactive change to
          the retained metrics. A new live run would require a new immutable
          artifact.
        </p>
      </section>

      <section className="panel">
        <h2>Inspect the receipt, not a claim</h2>
        <div className="linkRow">
          <Link href="/runs/run_hero_cohere_live_20260812T145023Z/">
            Open recorded run
          </Link>
          <Link href="/snapshots/hero-cohere-live.json">Raw live snapshot</Link>
          <Link href="/snapshots/ab-site-current.json">Raw A/B projection</Link>
          <Link href="/results/ab/">Read measured A/B</Link>
          <a href="https://docs.cohere.com/docs/command-a-plus">
            Command A+ docs ↗
          </a>
          <a href="https://docs.cohere.com/docs/cohere-embed">
            Embed v4 docs ↗
          </a>
          <a href="https://docs.cohere.com/docs/rerank">Rerank docs ↗</a>
          <a href="https://docs.cohere.com/v2/docs/tool-use-citations">
            Tool citations docs ↗
          </a>
          <a href="https://docs.cohere.com/v2/docs/structured-outputs">
            Structured outputs docs ↗
          </a>
        </div>
      </section>
    </main>
  );
}
