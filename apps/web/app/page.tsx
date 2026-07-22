import snapshot from "../public/snapshots/hero-foundation.json";
import React from "react";
import { ApprovalPanel } from "./approval-panel";

const contextStatus = new Map(
  snapshot.context.map((item) => [item.operation, item.status]),
);

export default function Home() {
  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="ResolveFlow Replay home">
          <span className="brandMark">RF</span>
          <span>
            ResolveFlow <strong>Replay</strong>
          </span>
        </a>
        <div className="recorded">
          <span aria-hidden="true" /> Recorded fixture
        </div>
      </header>

      <section className="hero" id="top">
        <p className="eyebrow">DEPLOYMENT GATE FOR ENTERPRISE AGENTS</p>
        <h1>A convincing answer is not a release decision.</h1>
        <p className="lede">
          One synthetic payments incident travels from operational intake to
          cited resolution through a deterministic, inspectable path.
        </p>
        <div className="provenance" aria-label="Snapshot provenance">
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
        </div>
      </section>

      <section className="workspace" aria-label="Recorded incident resolution">
        <aside className="caseRail">
          <div className="sectionTitle">
            <span className="pulse" /> Active incident
          </div>
          <div className="severity">HIGH SEVERITY</div>
          <h2>Card failures after routing rollout</h2>
          <dl>
            <div>
              <dt>Tenant</dt>
              <dd>
                HelioPay <small>SYNTHETIC</small>
              </dd>
            </div>
            <div>
              <dt>Region</dt>
              <dd>{snapshot.case.region}</dd>
            </div>
            <div>
              <dt>Service</dt>
              <dd>{snapshot.case.service}</dd>
            </div>
            <div>
              <dt>Error</dt>
              <dd>
                <code>{snapshot.case.error_code}</code>
              </dd>
            </div>
          </dl>
          <div className="slackCard">
            <div className="avatar">MC</div>
            <div>
              <strong>Maya Chen</strong>
              <span> 10:22</span>
              <p>{snapshot.case.raw_text}</p>
            </div>
          </div>
          <p className="simulationLabel">
            Slack-style simulation · not a real Slack workspace
          </p>
        </aside>

        <article className="resolution">
          <div className="sectionTitle">Verified resolution</div>
          <div className="routeRow">
            <span>ROUTE</span>
            <strong>{snapshot.response.route}</strong>
            <b>DETERMINISTICALLY VERIFIED</b>
          </div>
          <h2>Verified evidence graph</h2>
          <p>{snapshot.response.summary}</p>
          <ol className="steps">
            {snapshot.response.recommended_steps.map((step, index) => (
              <li key={step}>
                <span>{index + 1}</span>
                {step}
              </li>
            ))}
          </ol>
          <div className="unknown">
            <strong>Known unknown</strong>
            <p>{snapshot.response.unknowns[0]}</p>
          </div>
          <h3>Cited evidence</h3>
          <div className="citations">
            {snapshot.response.citations.map((citation) => (
              <details key={citation.citation_id}>
                <summary>
                  <span>{citation.title}</span>
                  <small>
                    {citation.version} · {citation.locator}
                  </small>
                </summary>
                <p>{citation.excerpt}</p>
              </details>
            ))}
          </div>
          <ApprovalPanel proposal={snapshot.action} />
        </article>

        <aside className="trace">
          <div className="sectionTitle">Chronological trace</div>
          <p className="traceIntro">
            Observable events only. No hidden reasoning.
          </p>
          <ol>
            {snapshot.trace.map((event) => (
              <li key={event.event_id}>
                <span
                  className={event.outcome === "ok" ? "done" : "attention"}
                  aria-label={event.outcome}
                />
                <div>
                  <small>{event.component}</small>
                  <strong>{event.event_name.replaceAll(".", " ")}</strong>
                </div>
                <code>{String(event.sequence).padStart(2, "0")}</code>
              </li>
            ))}
          </ol>
          <div className="contextChecks">
            <p>
              <span>Customer profile</span>
              <b>{contextStatus.get("get_customer_profile")}</b>
            </p>
            <p>
              <span>Rollout record</span>
              <b>{contextStatus.get("get_rollouts")}</b>
            </p>
            <p>
              <span>Active cluster</span>
              <b className="missing">
                {contextStatus.get("get_active_clusters")}
              </b>
            </p>
          </div>
          <a className="rawLink" href="snapshots/hero-foundation.json">
            Inspect raw snapshot →
          </a>
        </aside>
      </section>

      <footer>
        <span>
          Governed recorded fixture · no Cohere key required · no external
          writes
        </span>
        <code>{snapshot.content_hash.slice(0, 24)}…</code>
      </footer>
    </main>
  );
}
