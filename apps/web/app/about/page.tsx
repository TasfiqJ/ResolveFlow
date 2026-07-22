export default function AboutPage() {
  return (
    <main className="pageShell" id="main-content">
      <header className="pageIntro">
        <p className="eyebrow">ABOUT RESOLVEFLOW REPLAY</p>
        <h1>Replay is the product.</h1>
        <p>
          The incident agent is a realistic test subject for a harder question:
          does the complete enterprise workflow deserve a constrained pilot?
        </p>
      </header>
      <section className="twoColumn">
        <article className="panel">
          <h2>What this demonstrates</h2>
          <p>
            Product judgment across evidence access, retrieval, grounded
            responses, human approvals, failure recovery, auditability, and
            release governance.
          </p>
        </article>
        <article className="panel">
          <h2>Honest limitations</h2>
          <p>
            Synthetic domain data only. This technical preview does not claim
            customer validation, human scoring, fluent-language signoff, a
            live provider result, or a real Slack/Jira integration result.
          </p>
        </article>
      </section>
      <section className="panel">
        <h2>Artifacts</h2>
        <div className="linkRow">
          <a href="https://github.com/TasfiqJ/ResolveFlow">Source repository</a>
          <a href="results/">Evaluation status</a>
          <a href="architecture/">Architecture</a>
          <a href="methodology/">Methodology</a>
        </div>
      </section>
    </main>
  );
}
