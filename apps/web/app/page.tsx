import type { CSSProperties } from "react";
import integrity from "../public/snapshots/evaluation-integrity-audit.json";
import snapshot from "../public/snapshots/hero-foundation.json";

const starField = [
  [8, 18, 0],
  [14, 72, 1.4],
  [19, 41, 0.8],
  [27, 13, 2.2],
  [32, 83, 0.3],
  [39, 29, 1.7],
  [47, 64, 2.8],
  [53, 9, 0.6],
  [58, 88, 2],
  [66, 22, 1.1],
  [71, 53, 2.5],
  [78, 79, 0.4],
  [84, 35, 1.9],
  [91, 16, 0.9],
  [94, 68, 2.7],
] as const;

const systemLayers = [
  ["01", "INTAKE", "Typed case"],
  ["02", "AUTH", "Filter first"],
  ["03", "RETRIEVE", "Rank evidence"],
  ["04", "VERIFY", "Close claims"],
  ["05", "APPROVE", "Bind payload"],
  ["06", "REPLAY", "Break safely"],
] as const;

const engineeringCards = [
  {
    code: "ACL.01",
    title: "Authorization before retrieval",
    copy: "Restricted evidence is removed before search, ranking, caching, or model context. A role downgrade cannot widen access.",
    proof: "NEGATIVE SECURITY TESTS",
  },
  {
    code: "EVG.02",
    title: "A verifiable evidence graph",
    copy: "Every material claim closes over an authorized, current, exact source span. Missing facts remain explicit unknowns.",
    proof: "DETERMINISTIC CLAIM CLOSURE",
  },
  {
    code: "ACT.03",
    title: "Exactly-bound actions",
    copy: "A Jira proposal is inert until a human approves the exact payload digest. Retries reconcile before any second effect.",
    proof: "NO PUBLIC WRITE AUTHORITY",
  },
  {
    code: "RPL.04",
    title: "Production-path replay",
    copy: "The same Resolve orchestrator runs controlled mutations, compares builds, and evaluates hard failures before quality.",
    proof: "ONE SHARED CODE PATH",
  },
] as const;

const proofStats = [
  {
    value: `${integrity.attack_payload_control_pass_count}/${integrity.attack_payload_control_execution_count}`,
    label: "stored attack payloads exercising expected controls",
    note: "DETERMINISTIC CONTROL EXECUTIONS",
    href: "snapshots/evaluation-integrity-audit.json",
  },
  {
    value: "14",
    label: "hash-linked audit events",
    note: "RECORDED HERO RUN",
    href: "runs/run_hero_foundation_001/",
  },
  {
    value: `${integrity.security_matrix_full_replay_execution_count}/${integrity.security_matrix_declared_count}`,
    label: "security matrix cells executed as full Replays",
    note: "DECLARATION IS NOT EXECUTION",
    href: "snapshots/evaluation-integrity-audit.json",
  },
  {
    value: "05",
    label: "reversible database migrations",
    note: "POSTGRESQL + PGVECTOR",
    href: "https://github.com/TasfiqJ/ResolveFlow/tree/main/migrations/versions",
  },
] as const;

const buildScope = [
  "Threat model and system architecture",
  "Hybrid retrieval with pre-search ACLs",
  "Bounded agent loop and typed tools",
  "Claim, citation, and conflict verifier",
  "Approval, idempotency, and worker recovery",
  "Replay compiler and hard-first release gate",
  "Static public product, CI, and restore path",
] as const;

export default function Home() {
  return (
    <main className="performancePage" id="main-content">
      <section className="performanceHero" id="top">
        <div className="stars" aria-hidden="true">
          {starField.map(([left, top, delay]) => (
            <span
              key={`${left}-${top}`}
              style={
                {
                  "--star-left": `${left}%`,
                  "--star-top": `${top}%`,
                  "--star-delay": `${delay}s`,
                } as CSSProperties
              }
            />
          ))}
        </div>
        <span className="frameCorner frameTopLeft" aria-hidden="true" />
        <span className="frameCorner frameTopRight" aria-hidden="true" />
        <span className="frameCorner frameBottomLeft" aria-hidden="true" />
        <span className="frameCorner frameBottomRight" aria-hidden="true" />

        <div className="heroTelemetry heroTelemetryLeft" aria-hidden="true">
          <span>SYS://RESOLVEFLOW</span>
          <span>CASE_STUDY.001</span>
        </div>
        <div className="heroTelemetry heroTelemetryRight" aria-hidden="true">
          <span>43.6532° N</span>
          <span>79.3832° W</span>
        </div>

        <div className="heroGrid">
          <div className="heroCopy">
            <div className="technicalRule">
              <span>001</span>
              <i />
              <b>FULL-STACK AI SAFETY ENGINEERING</b>
            </div>
            <p className="heroByline">BUILT END-TO-END BY TASFIQ JASIMUDDIN</p>
            <h1>
              I BUILT THE
              <span>RELEASE GATE</span>
              AI AGENTS ARE MISSING.
            </h1>
            <p className="performanceLede">
              ResolveFlow stress-tests a workplace AI agent under revoked
              access, hostile evidence, missing context, and connector failure—
              then returns a release verdict backed by an auditable trace.
            </p>
            <div className="performanceActions">
              <a className="signalButton signalPrimary" href="#demo">
                <span>RUN THE RECORDED REPLAY</span>
                <b aria-hidden="true">↘</b>
              </a>
              <a
                className="signalButton"
                href="https://github.com/TasfiqJ/ResolveFlow"
              >
                <span>VIEW SOURCE</span>
                <b aria-hidden="true">↗</b>
              </a>
            </div>
            <div className="heroStack" aria-label="Core technologies">
              <span>PYTHON</span>
              <span>FASTAPI</span>
              <span>POSTGRESQL</span>
              <span>PGVECTOR</span>
              <span>NEXT.JS</span>
            </div>
          </div>

          <div className="systemVisual" aria-label="Animated replay gate model">
            <div className="visualLabel visualLabelTop">
              <span>REPLAY ENGINE</span>
              <b>ACTIVE</b>
            </div>
            <div className="orbit orbitOuter" />
            <div className="orbit orbitMiddle" />
            <div className="orbit orbitInner" />
            <div className="crosshair crosshairHorizontal" />
            <div className="crosshair crosshairVertical" />
            <div className="agentCore">
              <small>BUILD</small>
              <strong>V1</strong>
              <span>GUARDED</span>
              <i />
            </div>
            <div className="orbitNode nodeAcl">
              <small>ACL</small>
              <b>PASS</b>
            </div>
            <div className="orbitNode nodeEvidence">
              <small>EVIDENCE</small>
              <b>3/3</b>
            </div>
            <div className="orbitNode nodeAction">
              <small>WRITE</small>
              <b>INERT</b>
            </div>
            <div className="orbitNode nodeReplay">
              <small>REPLAY</small>
              <b>04</b>
            </div>
            <div className="scanBeam" />
            <div className="visualLabel visualLabelBottom">
              <span>HARD GATES FIRST</span>
              <b>SHIP / LIMIT / STOP</b>
            </div>
          </div>
        </div>

        <div className="systemRail">
          <span>
            <i /> SYSTEM.ACTIVE
          </span>
          <span>RECORDED SYNTHETIC FIXTURE</span>
          <span>14 AUDIT EVENTS</span>
          <span>NO EXTERNAL WRITES</span>
          <span>TECHNICAL PREVIEW</span>
        </div>
      </section>

      <section className="manifestoSection" id="what-it-does">
        <div className="sectionCode">[01/06] // THE THESIS</div>
        <p className="manifestoLead">MOST AI DEMOS SHOW YOU AN ANSWER.</p>
        <h2>
          I BUILT THE SYSTEM THAT DECIDES
          <em>IF THE AGENT SHOULD SHIP.</em>
        </h2>
        <div className="manifestoGrid">
          <p>
            A convincing response can still be unsafe. The model may have read
            restricted data, trusted a malicious document, guessed a missing
            fact, or prepared an action nobody approved.
          </p>
          <p>
            ResolveFlow makes the invisible engineering visible. It captures the
            evidence path, replays the system under controlled failure, and
            blocks a release when a hard invariant breaks.
          </p>
        </div>
      </section>

      <section className="controlRoom" id="demo">
        <div className="sectionHeader">
          <div>
            <div className="sectionCode">[02/06] // REPLAY CONTROL ROOM</div>
            <h2>ONE INCIDENT. TWO BUILDS. ONE RELEASE DECISION.</h2>
          </div>
          <p>
            Real stored output from a checksummed synthetic development fixture.
            No provider call or external service is required.
          </p>
        </div>

        <div className="controlConsole">
          <div className="consoleTopbar">
            <span>
              <i /> RECORDED.RUN
            </span>
            <code>{snapshot.build_id}</code>
            <span>CASE: {snapshot.case.error_code}</span>
          </div>

          <div className="consoleGrid">
            <article className="incidentConsole">
              <div className="consoleIndex">01 // INTAKE</div>
              <div className="severityReadout">HIGH SEVERITY</div>
              <h3>CARD FAILURES AFTER ROUTING ROLLOUT</h3>
              <div className="operatorMessage">
                <span>MC</span>
                <p>{snapshot.case.raw_text}</p>
              </div>
              <dl>
                <div>
                  <dt>TENANT</dt>
                  <dd>HELIOPAY [SYNTHETIC]</dd>
                </div>
                <div>
                  <dt>SERVICE</dt>
                  <dd>{snapshot.case.service}</dd>
                </div>
                <div>
                  <dt>REGION</dt>
                  <dd>{snapshot.case.region}</dd>
                </div>
              </dl>
            </article>

            <article className="verificationConsole">
              <div className="consoleIndex">02 // VERIFIED RESOLVE</div>
              <div className="routeReadout">
                <small>ROUTE</small>
                <strong>{snapshot.response.route}</strong>
                <b>VERIFIED</b>
              </div>
              <div className="claimReadout">
                <span>✓</span>
                <p>
                  <small>KNOWN FACT</small>
                  {snapshot.response.summary}
                </p>
              </div>
              <div className="claimReadout">
                <span>→</span>
                <p>
                  <small>NEXT SAFE STEP</small>
                  {snapshot.response.recommended_steps[0]}
                </p>
              </div>
              <div className="claimReadout unknownReadout">
                <span>?</span>
                <p>
                  <small>EXPLICIT UNKNOWN</small>
                  {snapshot.response.unknowns[0]}
                </p>
              </div>
              <div className="citationReadout">
                <b>{snapshot.response.citations.length}</b>
                <span>EXACT CITATIONS</span>
                <i />
                <b>0</b>
                <span>EXTERNAL WRITES</span>
              </div>
            </article>

            <article className="gateConsole">
              <div className="consoleIndex">03 // ADVERSARIAL REPLAY</div>
              <p className="mutationLabel">
                MUTATION: <b>ROLE_DOWNGRADE</b>
              </p>
              <div className="buildComparison">
                <div className="buildReadout unsafeReadout">
                  <span>BASELINE</span>
                  <strong>unsafe-v0</strong>
                  <div>
                    <i style={{ width: "100%" }} />
                  </div>
                  <p>1 RESTRICTED CANDIDATE ENTERED RETRIEVAL</p>
                  <b>NO SHIP</b>
                </div>
                <div className="buildReadout guardedReadout">
                  <span>CANDIDATE</span>
                  <strong>guarded-v1</strong>
                  <div>
                    <i style={{ width: "0%" }} />
                  </div>
                  <p>0 RESTRICTED CANDIDATES ENTERED RETRIEVAL</p>
                  <b>NO SHIP</b>
                </div>
              </div>
              <p className="gateCaveat">
                BLOCKED: hard action/deployment evidence is unexercised and 36
                draft truth IDs collapse to one semantic template.
              </p>
            </article>
          </div>

          <div className="consoleFooter">
            <span>TRACE.HASH {snapshot.content_hash.slice(0, 22)}…</span>
            <div>
              <a href="replay/">OPEN FULL REPLAY ↗</a>
              <a href="runs/run_hero_foundation_001/">
                INSPECT 14-EVENT TRACE ↗
              </a>
            </div>
          </div>
        </div>
      </section>

      <section className="systemSection" id="engineering">
        <div className="sectionHeader">
          <div>
            <div className="sectionCode">[03/06] // SYSTEM ARCHITECTURE</div>
            <h2>NOT A PROMPT. A GOVERNED SYSTEM.</h2>
          </div>
          <p>
            Each safety property lives in application code, typed contracts,
            persisted state, and tests—not a polite instruction to the model.
          </p>
        </div>

        <div className="pipeline" aria-label="ResolveFlow system pipeline">
          {systemLayers.map(([number, name, note], index) => (
            <article key={number}>
              <small>{number}</small>
              <strong>{name}</strong>
              <span>{note}</span>
              {index < systemLayers.length - 1 && <i aria-hidden="true">→</i>}
            </article>
          ))}
        </div>

        <div className="engineeringGrid">
          {engineeringCards.map((card) => (
            <article key={card.code}>
              <div>
                <span>{card.code}</span>
                <i />
              </div>
              <h3>{card.title}</h3>
              <p>{card.copy}</p>
              <small>✓ {card.proof}</small>
            </article>
          ))}
        </div>
        <a className="inlineSignal" href="architecture/">
          EXPLORE THE COMPLETE ARCHITECTURE <span>↗</span>
        </a>
      </section>

      <section className="proofWall" id="proof">
        <div className="sectionCode">[04/06] // ENGINEERING PROOF</div>
        <div className="proofHeadline">
          <h2>THE RECEIPTS, NOT THE PITCH.</h2>
          <p>
            Every number below comes from the versioned repository or recorded
            fixture. No invented users, reviewer scores, provider metrics, or
            production claims.
          </p>
        </div>
        <div className="statWall">
          {proofStats.map((stat) => (
            <a href={stat.href} key={stat.label}>
              <strong>{stat.value}</strong>
              <span>{stat.label}</span>
              <small>
                {stat.note} <b aria-hidden="true">↗</b>
              </small>
            </a>
          ))}
        </div>
        <div className="evidenceStrip">
          <div>
            <span>AUTOMATED SUITE</span>
            <b>PASS</b>
          </div>
          <div>
            <span>UNSAFE SEEDED GATE</span>
            <b>BLOCKS</b>
          </div>
          <div>
            <span>PUBLIC SECRET SCAN</span>
            <b>PASS</b>
          </div>
          <div>
            <span>HUMAN REVIEW</span>
            <b className="pendingProof">0 REVIEWERS / 0 CASES</b>
          </div>
        </div>
        <p className="proofDisclosure">
          Technical preview only; human validation remains pending. ResolveFlow
          does not claim live-provider quality, real connector success,
          multilingual performance, or a final production release verdict.
        </p>
      </section>

      <section className="builderSection">
        <div className="sectionCode">[05/06] // THE BUILDER</div>
        <div className="builderGrid">
          <div className="builderStatement">
            <p>DESIGNED + ENGINEERED BY</p>
            <h2>
              TASFIQ
              <span>JASIMUDDIN</span>
            </h2>
            <p className="builderCopy">
              I built ResolveFlow to prove I can take an AI system beyond the
              demo: model boundaries, data access, distributed reliability,
              evaluation, security, product design, CI, and public delivery.
            </p>
            <div className="builderActions">
              <a
                className="signalButton signalPrimary"
                href="https://github.com/TasfiqJ/ResolveFlow"
              >
                REVIEW THE SOURCE <b>↗</b>
              </a>
              <a className="signalButton" href="about/">
                READ THE CASE STUDY <b>→</b>
              </a>
            </div>
          </div>
          <div className="scopePanel">
            <div className="scopeHeader">
              <span>END-TO-END OWNERSHIP</span>
              <b>07 SYSTEMS</b>
            </div>
            <ol>
              {buildScope.map((item, index) => (
                <li key={item}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <p>{item}</p>
                  <b>COMPLETE</b>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </section>

      <section className="deepDiveSection">
        <div className="sectionCode">[06/06] // GO DEEPER</div>
        <h2>FOLLOW THE EVIDENCE.</h2>
        <div className="deepDiveLinks">
          <a href="replay/">
            <span>01</span>
            <strong>Replay lab</strong>
            <small>Compare the unsafe and guarded builds</small>
            <b>↗</b>
          </a>
          <a href="runs/run_hero_foundation_001/">
            <span>02</span>
            <strong>Audit trace</strong>
            <small>Inspect every observable event</small>
            <b>↗</b>
          </a>
          <a href="results/">
            <span>03</span>
            <strong>Release scorecard</strong>
            <small>See exact evidence and missing validation</small>
            <b>↗</b>
          </a>
          <a href="methodology/">
            <span>04</span>
            <strong>Evaluation method</strong>
            <small>Read the hard-first gate design</small>
            <b>↗</b>
          </a>
          <a href="audit/">
            <span>05</span>
            <strong>Senior engineering audit</strong>
            <small>See the gaps, fixes, and remaining promotion gates</small>
            <b>↗</b>
          </a>
        </div>
      </section>

      <footer className="performanceFooter">
        <div className="footerBrand">
          <span>RF</span>
          <div>
            <b>RESOLVEFLOW</b>
            <small>AI AGENT RELEASE GATE</small>
          </div>
        </div>
        <p>BUILT IN TORONTO // PUBLISHED AS A RECORDED TECHNICAL PREVIEW</p>
        <div>
          <a href="https://github.com/TasfiqJ/ResolveFlow">GITHUB ↗</a>
          <a href="#top">TOP ↑</a>
        </div>
      </footer>
    </main>
  );
}
