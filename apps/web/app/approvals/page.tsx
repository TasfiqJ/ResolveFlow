import snapshot from "../../public/snapshots/hero-foundation.json";
import { ApprovalPanel } from "../approval-panel";

export default function ApprovalsPage() {
  return (
    <main className="pageShell" id="main-content">
      <header className="pageIntro">
        <p className="eyebrow">APPROVALS</p>
        <h1>Pending Jira proposals</h1>
        <p>
          A proposal is inert until a human approves the exact payload digest.
          Retries reconcile before any second effect. This is the real proposal
          object from the recorded hero run — approving or rejecting it below
          only changes local component state; the Jira adapter is disabled and
          no external write can occur.
        </p>
      </header>

      <ApprovalPanel proposal={snapshot.action} />
    </main>
  );
}
