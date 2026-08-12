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
    value: "06",
    label: "reversible database migrations",
    note: "POSTGRESQL + PGVECTOR",
    href: "https://github.com/TasfiqJ/ResolveFlow/tree/fix/backend-audit/migrations/versions",
  },
] as const;

const deliverySurfaces = [
  {
    label: "PUBLIC SITE",
    title: "Static, credential-free evidence viewer",
    copy: "This GitHub Pages build serves Next.js pages and checksummed JSON snapshots. It does not expose an API, a database, a model key, or a Slack/Jira connection to visitors.",
    state: "WHAT A RECRUITER CAN INSPECT NOW",
  },
  {
    label: "LOCAL RUNTIME",
    title: "A governed Cohere composition behind the artifact",
    copy: "The local stack composes Cohere Chat, Embed v4, and Rerank v4 as one authorized runtime alongside FastAPI, a worker, PostgreSQL with pgvector, typed contracts, migrations, and a shared Resolve/Replay orchestrator.",
    state: "IMPLEMENTED LOCALLY · NOT PUBLICLY HOSTED",
  },
  {
    label: "EVIDENCE BOUNDARY",
    title: "Fail closed when the proof is incomplete",
    copy: "The published comparison is a synthetic development fixture. Human review, held-out evaluation, live-provider quality, real connector success, and a final release verdict remain unclaimed.",
    state: "TECHNICAL PREVIEW · NO SHIP",
  },
] as const;

const verificationStats = [
  ["149", "non-PostgreSQL tests", "credential-isolated recorded verification"],
  ["04", "PostgreSQL tests", "durable state and retrieval coverage"],
  ["24", "security tests", "access, tools, evidence, and public boundaries"],
  ["06", "migration revisions", "versioned persistence evolution"],
] as const;

const storyBeats = [
  {
    number: "01",
    label: "THE OPERATING PROBLEM",
    title: "A fluent answer can still be unsafe.",
    copy: "An agent can access data a user is no longer allowed to see, treat hostile text as an instruction, invent a key fact, or prepare an action no one approved.",
  },
  {
    number: "02",
    label: "THE FDE-STYLE INTERVENTION",
    title: "Work backward from the operator.",
    copy: "In an FDE-style delivery model, the starting point is the real workflow—not the model. ResolveFlow turns a messy payments report into typed intake, access rules, evidence contracts, narrow tools, approval before action, and observable recovery.",
  },
  {
    number: "03",
    label: "THE RESOLVE PATH",
    title: "Earn each recommendation from evidence.",
    copy: "The system checks access before search, ranks only authorized evidence, verifies key claims, shows what is still unknown, and keeps any Jira draft inactive until an operator approves it.",
  },
  {
    number: "04",
    label: "THE REPLAY PATH",
    title: "Test the system when conditions change.",
    copy: "Replay freezes one starting point, changes one condition such as a role downgrade, reruns the same path, compares builds, and blocks promotion when a hard rule fails or evidence is missing.",
  },
] as const;

const buildScope = [
  "FDE-style workflow mapping: incident → contracts → safe operator path",
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
              <b>STATIC CASE STUDY // LOCAL RUNTIME BUILT</b>
            </div>
            <p className="heroByline">BUILT END-TO-END BY TASFIQ JASIMUDDIN</p>
            <h1>
              I BUILT THE
              <span>RELEASE GATE</span>
              AI AGENTS ARE MISSING.
            </h1>
            <p className="performanceLede">
              ResolveFlow is a release gate for workplace AI agents. It tests
              access changes, hostile evidence, missing context, and connector
              failure—then returns a clear, auditable release decision.
            </p>
            <p className="fdeLede">
              Built as an FDE-style systems exercise: turn a messy payments
              issue into a clear, controlled workflow with typed contracts,
              authorized evidence, bounded tools, operator approval, and
              observable recovery.
            </p>
            <p className="heroDisclosure">
              You are viewing a credential-free GitHub Pages artifact: recorded
              evidence is public; the API, database, worker, optional Cohere
              runtime, and external connectors are not exposed here.
            </p>
            <div className="performanceActions">
              <a className="signalButton signalPrimary" href="#demo">
                <span>RUN THE RECORDED REPLAY</span>
                <b aria-hidden="true">↘</b>
              </a>
              <a className="signalButton" href="#deployment">
                <span>WHAT IS DEPLOYED?</span>
                <b aria-hidden="true">↓</b>
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

          <section
            className="releaseGateVisual"
            aria-label="How the release gate works"
          >
            <div className="gateVisualHeader">
              <span>HOW THE RELEASE GATE WORKS</span>
              <b>RECORDED REPLAY</b>
            </div>
            <div className="gateSteps">
              <article>
                <span>01</span>
                <h3>Check access</h3>
                <p>Use only evidence this operator is allowed to see.</p>
                <b>ACL PASS</b>
              </article>
              <article>
                <span>02</span>
                <h3>Verify evidence</h3>
                <p>Support key claims and clearly mark what is unknown.</p>
                <b>3 / 3 VERIFIED</b>
              </article>
              <article>
                <span>03</span>
                <h3>Require approval</h3>
                <p>Keep external actions inactive until a person approves.</p>
                <b>WRITE INERT</b>
              </article>
            </div>
            <div className="gateDecision">
              <div>
                <span>REPLAY MUTATION</span>
                <strong>ROLE DOWNGRADE</strong>
              </div>
              <i aria-hidden="true" />
              <div>
                <span>RELEASE DECISION</span>
                <strong>NO SHIP UNTIL VERIFIED</strong>
              </div>
            </div>
          </section>
        </div>

        <div className="systemRail">
          <span>
            <i /> PUBLIC.STATIC
          </span>
          <span>GITHUB PAGES EXPORT</span>
          <span>14-EVENT RECORDED SYNTHETIC TRACE</span>
          <span>LOCAL API + WORKER NOT EXPOSED</span>
          <span>NO EXTERNAL WRITES</span>
        </div>
      </section>

      <section className="manifestoSection" id="what-it-does">
        <div className="sectionCode">[01/08] // THE THESIS</div>
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

      <section className="storySection" id="story">
        <div className="sectionHeader">
          <div>
            <div className="sectionCode">[02/08] // THE STORY</div>
            <h2>FROM AN OPERATOR&apos;S PROBLEM TO A RELEASE DECISION.</h2>
          </div>
          <p>
            The goal is not a clever answer. It is a system a team can inspect,
            test, and decide whether it is ready for a small, controlled pilot.
          </p>
        </div>
        <div className="whyBuilt">
          <div>
            <span>WHY I BUILT RESOLVEFLOW</span>
            <h3>AI should earn trust before it earns autonomy.</h3>
          </div>
          <div>
            <p>
              Most AI demos stop at a polished answer. I wanted to build the
              harder part: the system a team needs before it lets an agent touch
              a real workflow.
            </p>
            <p>
              This is an FDE-style delivery project. Start with the
              operator&apos;s incident, translate it into contracts and
              integration boundaries, make failure visible, and leave the team
              with an auditable path to a controlled pilot.
            </p>
          </div>
        </div>
        <div className="storyGrid">
          {storyBeats.map((beat) => (
            <article key={beat.number}>
              <span>{beat.number}</span>
              <small>{beat.label}</small>
              <h3>{beat.title}</h3>
              <p>{beat.copy}</p>
            </article>
          ))}
        </div>
        <p className="storyOutcome">
          <b>THE HONEST OUTCOME:</b> guarded-v1 prevents the role-downgrade
          authorization failure, yet remains <b>NO SHIP</b> because required
          action, deployment, held-out, and human-review evidence is not
          complete. That refusal is the product working as intended.
        </p>
      </section>

      <section className="deploymentSection" id="deployment">
        <div className="sectionHeader">
          <div>
            <div className="sectionCode">[03/08] // DEPLOYMENT REALITY</div>
            <h2>PUBLIC BY DESIGN. LOCAL BY PROOF.</h2>
          </div>
          <p>
            This is not a disguised live demo. It is a static technical case
            study designed to let a recruiter inspect the system, its evidence,
            and its limits without granting a browser any operational access.
          </p>
        </div>

        <div className="deliveryGrid">
          {deliverySurfaces.map((surface) => (
            <article key={surface.label}>
              <span>{surface.label}</span>
              <h3>{surface.title}</h3>
              <p>{surface.copy}</p>
              <small>{surface.state}</small>
            </article>
          ))}
        </div>

        <div className="verificationLedger">
          <div>
            <span>RECORDED VERIFICATION</span>
            <h3>2026-07-26 · credential-isolated local evidence</h3>
            <p>
              These checks demonstrate engineering coverage, not production
              performance or a release certificate. Read the limits alongside
              the numbers.
            </p>
          </div>
          <div className="verificationStats">
            {verificationStats.map(([value, label, note]) => (
              <article key={label}>
                <strong>{value}</strong>
                <span>{label}</span>
                <small>{note}</small>
              </article>
            ))}
          </div>
          <a className="inlineSignal" href="results/">
            READ THE RELEASE SCORECARD <span>↗</span>
          </a>
        </div>
      </section>

      <section className="controlRoom" id="demo">
        <div className="sectionHeader">
          <div>
            <div className="sectionCode">[04/08] // REPLAY CONTROL ROOM</div>
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
            <div className="sectionCode">[05/08] // SYSTEM ARCHITECTURE</div>
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
        <div className="sectionCode">[06/08] // ENGINEERING PROOF</div>
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
        <div className="sectionCode">[07/08] // THE BUILDER</div>
        <div className="builderGrid">
          <div className="builderStatement">
            <p>DESIGNED + ENGINEERED BY</p>
            <h2>
              TASFIQ
              <span>JASIMUDDIN</span>
            </h2>
            <p className="builderCopy">
              I built ResolveFlow as an FDE-style delivery exercise: take a
              messy operational workflow and turn it into typed contracts,
              controlled data access, bounded Cohere orchestration, approval
              semantics, durable recovery, evaluation, and an inspectable public
              artifact.
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
              <b>08 SYSTEMS</b>
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
        <div className="sectionCode">[08/08] // GO DEEPER</div>
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
