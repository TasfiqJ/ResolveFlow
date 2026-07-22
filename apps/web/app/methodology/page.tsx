export default function MethodologyPage() {
  return (
    <main className="pageShell" id="main-content">
      <header className="pageIntro">
        <p className="eyebrow">METHODOLOGY</p>
        <h1>A release gate with receipts.</h1>
        <p>
          Inputs are frozen, one mutation is declared, hard invariants are
          scored first, and every proportion carries its numerator and
          denominator.
        </p>
      </header>
      <section className="methodSteps">
        {[
          [
            "01",
            "Freeze",
            "Clock, identity, ACL, corpus, model policy, connector, build, and hashes.",
          ],
          [
            "02",
            "Mutate",
            "Apply one typed condition without changing the latent incident truth.",
          ],
          [
            "03",
            "Run",
            "Execute the same Resolve orchestrator used by the interactive workflow.",
          ],
          [
            "04",
            "Score",
            "Evaluate deterministic safety gates before quality or operations.",
          ],
          [
            "05",
            "Compare",
            "Pair unsafe-v0 and guarded-v1 at the base-truth cluster level.",
          ],
          [
            "06",
            "Decide",
            "Emit SHIP, SHIP WITH LIMITS, or NO SHIP with failure links.",
          ],
        ].map(([n, title, detail]) => (
          <article key={n}>
            <code>{n}</code>
            <h2>{title}</h2>
            <p>{detail}</p>
          </article>
        ))}
      </section>
      <section className="panel">
        <h2>Validation status</h2>
        <p>
          The 36 candidate truths are synthetic-agent-authored and pending human
          review. The 200-scenario matrix is deterministic application-control
          coverage, not 200 live model attacks. Human review and multilingual
          signoff are both currently absent.
        </p>
      </section>
    </main>
  );
}
