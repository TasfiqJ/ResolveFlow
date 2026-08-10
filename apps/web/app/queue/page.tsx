import Link from "next/link";
import snapshot from "../../public/snapshots/hero-foundation.json";

const queueStats = [
  { label: "Open cases", value: "1" },
  { label: "Blocked", value: "0" },
  { label: "Pending approval", value: "1" },
  { label: "Recorded runs", value: "1" },
] as const;

export default function QueuePage() {
  return (
    <main className="pageShell" id="main-content">
      <header className="pageIntro">
        <p className="eyebrow">INCIDENT QUEUE</p>
        <h1>Cases awaiting a decision</h1>
        <p>
          The queue lists every case ResolveFlow has a recorded run for. This
          preview ships with one checksummed synthetic case — the same run shown
          throughout the site — rather than invented volume.
        </p>
      </header>

      <div className="statTiles">
        {queueStats.map((stat) => (
          <div className="card elev-sm" key={stat.label}>
            <span className="card-kicker">{stat.label}</span>
            <span className="card-title">{stat.value}</span>
          </div>
        ))}
      </div>

      <div className="card elev-sm tableCard">
        <table className="table">
          <thead>
            <tr>
              <th>Case</th>
              <th>Tenant</th>
              <th>Service</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>
                <Link
                  className="rowLink"
                  href={`/queue/${snapshot.case.case_id}/`}
                  style={{ fontWeight: 600 }}
                >
                  {snapshot.case.error_code}
                </Link>
              </td>
              <td>{snapshot.case.tenant_id}</td>
              <td>{snapshot.case.service}</td>
              <td>
                <span className="tag tag-danger">{snapshot.case.severity}</span>
              </td>
              <td>
                <span className="tag tag-outline">
                  {snapshot.action.state.replaceAll("_", " ")}
                </span>
              </td>
              <td className="text-muted">{snapshot.case.received_at}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p
        className="text-muted"
        style={{ fontSize: 12, marginTop: "var(--space-4)" }}
      >
        RECORDED SYNTHETIC FIXTURE · {snapshot.case.tenant_id} is a synthetic
        tenant; no real customer data appears in this queue.
      </p>
    </main>
  );
}
