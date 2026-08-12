import Link from "next/link";
import integrity from "../../public/snapshots/evaluation-integrity-audit.json";

const findings = [
  {
    concern: "Unobserved release invariants were credited as zero failures",
    response:
      "Gate 1.1 records observed, not-exercised, and not-verified evidence separately. Missing hard-gate evidence now forces NO SHIP.",
    status: "BRIDGED",
  },
  {
    concern: "Thirty-six truth IDs were one duplicated semantic template",
    response:
      "A checksummed integrity audit fingerprints truth semantics and blocks dataset integrity. The project now claims 1 unique template, not 36 cases.",
    status: "EXPOSED",
  },
  {
    concern: "Two hundred security IDs had zero full Replay executions",
    response: `${integrity.security_matrix_full_replay_execution_count}/200 cells now have recorded-fixture production-path Replay evidence: ${integrity.security_matrix_pass_count} passed and ${integrity.security_matrix_failure_count} remain open. Every per-cell result is retained in the published snapshot.`,
    status: "EXECUTED",
  },
  {
    concern:
      "Live mode switched chat but left fixture retrieval adapters in place",
    response:
      "One composition root now switches chat, embeddings, and reranking together, applies configured budgets/models, and embeds only ACL-authorized candidates.",
    status: "BRIDGED",
  },
  {
    concern: "Live runs could be mislabeled as recorded fixtures",
    response:
      "Run provenance is now derived from the active provider, and audit-chain verification recomputes event hashes instead of trusting stored pointers.",
    status: "BRIDGED",
  },
] as const;

const openGates = [
  "Truth catalog integrity: 36 draft IDs currently collapse to 1 semantic template",
  ...(integrity.security_matrix_failure_count
    ? [
        `Security matrix execution: ${integrity.security_matrix_failure_count} failing cells remain open`,
      ]
    : []),
  "Action hard gates are not exercised by the published role-downgrade Replay",
  "No live Cohere run or provider latency, quality, usage, or cost evidence",
  "No practitioner review: 0 reviewers and 0 reviewed cases",
  "No locked held-out dataset or final production release verdict",
  "No real Slack workspace event or Jira development-site write",
  "Fixture API state is in memory; PostgreSQL durability exists in repositories and worker tests but is not the API runtime composition",
  "No fluent-human multilingual validation",
] as const;

export default function AuditPage() {
  return (
    <main className="pageShell" id="main-content">
      <header className="pageIntro">
        <p className="eyebrow">SENIOR ENGINEERING AUDIT</p>
        <h1>The gaps are part of the evidence.</h1>
        <p>
          A portfolio project is only credible when its controls, tests, public
          claims, and release process agree. This page records the sharpest
          concerns found in a skeptical review and what still prevents a
          validated release.
        </p>
      </header>

      <section className="auditFindings" aria-labelledby="closed-findings">
        <div className="auditSectionHeading">
          <p className="eyebrow">CREDIBILITY HARDENING</p>
          <h2 id="closed-findings">Issues that were worth fixing</h2>
        </div>
        {findings.map((finding, index) => (
          <article key={finding.concern}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <div>
              <small>REVIEW CONCERN</small>
              <h3>{finding.concern}</h3>
              <p>{finding.response}</p>
            </div>
            <b>{finding.status}</b>
          </article>
        ))}
      </section>

      <section className="openGatePanel" aria-labelledby="open-gates">
        <div>
          <p className="eyebrow">PROMOTION BLOCKERS</p>
          <h2 id="open-gates">What still prevents a validated release</h2>
          <p>
            These gaps require genuine people, credentials, locked evaluation
            chronology, or external observations. They are not replaced with
            generated evidence.
          </p>
        </div>
        <ol>
          {openGates.map((gate, index) => (
            <li key={gate}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <p>{gate}</p>
              <b>OPEN</b>
            </li>
          ))}
        </ol>
      </section>

      <section className="panel">
        <h2>Audit the audit</h2>
        <p>
          The repository keeps the complete limitation register, acceptance
          matrix, decision log, and release checks in version control.
        </p>
        <div className="linkRow">
          <a href="https://github.com/TasfiqJ/ResolveFlow/blob/main/docs/KNOWN_LIMITATIONS.md">
            Known limitations
          </a>
          <a href="https://github.com/TasfiqJ/ResolveFlow/blob/main/docs/ACCEPTANCE_MATRIX.md">
            Acceptance matrix
          </a>
          <a href="https://github.com/TasfiqJ/ResolveFlow/blob/main/docs/DECISIONS.md">
            Decision log
          </a>
          <Link href="/results/">Current evidence</Link>
        </div>
      </section>
    </main>
  );
}
