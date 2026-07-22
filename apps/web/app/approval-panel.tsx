"use client";

import React, { useState } from "react";

type Proposal = {
  proposal_id: string | null;
  state: string;
  summary: string;
  team: string;
  priority: string;
  verified_description: string;
  evidence_refs: string[];
  unknowns: string[];
  risk: string;
  expires_at: string | null;
  payload_digest: string | null;
  idempotency_key: string | null;
  permission_required: string;
};

export function ApprovalPanel({ proposal }: { proposal: Proposal }) {
  const [state, setState] = useState(proposal.state);
  const [issueKey, setIssueKey] = useState<string | null>(null);

  return (
    <section className="proposal" aria-live="polite">
      <div className="proposalHeader">
        <span>INERT JIRA PROPOSAL · SYNTHETIC CONNECTOR</span>
        <strong>{proposal.summary}</strong>
        <small>
          {proposal.team} · {proposal.priority} priority · {proposal.risk} risk
        </small>
      </div>
      <details>
        <summary>Inspect exact approval payload</summary>
        <p>{proposal.verified_description}</p>
        <dl>
          <div>
            <dt>Evidence</dt>
            <dd>{proposal.evidence_refs.join(", ")}</dd>
          </div>
          <div>
            <dt>Unknowns</dt>
            <dd>{proposal.unknowns.join(" ")}</dd>
          </div>
          <div>
            <dt>Expires</dt>
            <dd>{proposal.expires_at ?? "not proposed"}</dd>
          </div>
          <div>
            <dt>Payload digest</dt>
            <dd>
              <code>{proposal.payload_digest}</code>
            </dd>
          </div>
        </dl>
      </details>
      <div className="proposalState">
        <b>{state.replaceAll("_", " ").toUpperCase()}</b>
        {issueKey ? <code>{issueKey}</code> : null}
      </div>
      <div className="proposalActions">
        {state === "pending_approval" ? (
          <>
            <button type="button" onClick={() => setState("approved")}>
              Simulate exact approval
            </button>
            <button
              className="secondary"
              type="button"
              onClick={() => setState("rejected")}
            >
              Reject proposal
            </button>
          </>
        ) : null}
        {state === "approved" ? (
          <button
            type="button"
            onClick={() => {
              setIssueKey("SYN-1");
              setState("complete");
            }}
          >
            Run synthetic connector
          </button>
        ) : null}
      </div>
      <p className="proposalNotice">
        Recorded UI simulation only. The real Jira adapter is disabled and no
        external write can occur.
      </p>
    </section>
  );
}
