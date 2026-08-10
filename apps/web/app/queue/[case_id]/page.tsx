import Link from "next/link";
import snapshot from "../../../public/snapshots/hero-foundation.json";

export function generateStaticParams() {
  return [{ case_id: snapshot.case.case_id }];
}

export default function CaseDetailPage() {
  return (
    <main className="pageShell" id="main-content">
      <Link
        href="/queue/"
        className="navAction"
        style={{ marginBottom: "var(--space-4)", display: "inline-flex" }}
      >
        ← Back to queue
      </Link>

      <header className="pageIntro">
        <p className="eyebrow">
          {snapshot.case.error_code} · {snapshot.case.tenant_id.toUpperCase()}{" "}
          [SYNTHETIC]
        </p>
        <h1>Card failures after routing rollout</h1>
        <p>
          {snapshot.response.route} · {snapshot.case.region} · reported by{" "}
          {snapshot.case.reporter}
        </p>
      </header>

      <div className="twoColumn">
        <article className="card elev-sm">
          <span className="card-kicker">Verified response</span>
          <p>
            <b>Route</b> — {snapshot.response.route}
          </p>
          <p className="card-body">{snapshot.response.summary}</p>
          <div className="hr" />
          <span className="card-kicker">Known unknown</span>
          <p className="card-body">{snapshot.response.unknowns[0]}</p>
        </article>
        <article className="card elev-sm">
          <span className="card-kicker">Action boundary</span>
          <p>
            <span className="tag tag-outline">
              {snapshot.action.state.replaceAll("_", " ")}
            </span>
          </p>
          <p className="card-body">
            A {snapshot.action.action_type.replaceAll("_", " ")} proposal is
            prepared and inert until a human approves the exact payload digest.
          </p>
          <Link className="btn btn-primary btn-block" href="/approvals/">
            Review proposal
          </Link>
        </article>
      </div>

      <div className="card elev-sm tableCard">
        <div style={{ padding: "var(--space-3)" }}>
          <span className="card-kicker">Evidence</span>
        </div>
        <table className="table">
          <thead>
            <tr>
              <th>Source</th>
              <th>Span</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {snapshot.response.citations.map((citation) => (
              <tr key={citation.citation_id}>
                <td>{citation.title}</td>
                <td className="text-muted">{citation.locator}</td>
                <td>
                  <span className="tag tag-accent-2">
                    {citation.verifier_codes.includes("citation_supports_claim")
                      ? "verified"
                      : "unverified"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p
        className="text-muted"
        style={{ fontSize: 12, marginTop: "var(--space-4)" }}
      >
        RECORDED SYNTHETIC FIXTURE · full chronological trace at{" "}
        <Link href={`/runs/${snapshot.run_id}/`}>/runs/{snapshot.run_id}/</Link>
        .
      </p>
    </main>
  );
}
