"use client";

import Link from "next/link";
import { type KeyboardEvent, useRef, useState } from "react";

type Scenario = {
  id: string;
  label: string;
  evidenceLevel: "RECORDED" | "AUTOMATED TEST";
  title: string;
  summary: string;
  control: string;
  proof: string;
  href: string;
  linkLabel: string;
};

const scenarios: readonly Scenario[] = [
  {
    id: "role-downgrade",
    label: "Role downgrade",
    evidenceLevel: "RECORDED",
    title: "Restricted evidence is removed before ranking.",
    summary:
      "The published paired snapshot changes the operator role while keeping the incident and frozen manifest constant. unsafe-v0 admits one restricted candidate; guarded-v1 admits none.",
    control: "Pre-retrieval authorization",
    proof: "Paired checksummed development fixture",
    href: "/snapshots/replay-development-result.json",
    linkLabel: "Open raw result bundle",
  },
  {
    id: "baseline",
    label: "Baseline",
    evidenceLevel: "RECORDED",
    title: "The canonical incident resolves with an explicit unknown.",
    summary:
      "The stored hero run routes to Payments Platform, cites three exact sources, and preserves the missing cluster ID instead of guessing it.",
    control: "Claim closure and unknown handling",
    proof: "Recorded 14-event public trace",
    href: "/runs/run_hero_foundation_001/",
    linkLabel: "Inspect recorded trace",
  },
  {
    id: "malicious-runbook",
    label: "Malicious runbook",
    evidenceLevel: "AUTOMATED TEST",
    title: "Evidence text cannot widen tools, policy, or action authority.",
    summary:
      "Hostile instructions are exercised by deterministic security and Replay tests. No separate public run snapshot has been published for this condition.",
    control: "Untrusted-evidence boundary",
    proof: "Regression test; not a recorded public run",
    href: "https://github.com/TasfiqJ/ResolveFlow/blob/main/tests/security/test_evidence_cannot_mutate_policy.py",
    linkLabel: "Review the security test",
  },
  {
    id: "missing-evidence",
    label: "Missing evidence",
    evidenceLevel: "AUTOMATED TEST",
    title:
      "Missing decisive evidence forces review instead of a confident route.",
    summary:
      "A deterministic Replay regression removes the decisive artifact and asserts that the candidate produces no route or Jira proposal. No public snapshot is claimed.",
    control: "Abstention and proposal suppression",
    proof: "Replay regression; not a recorded public run",
    href: "https://github.com/TasfiqJ/ResolveFlow/blob/main/tests/replay/test_missing_decisive_evidence.py",
    linkLabel: "Review the Replay test",
  },
  {
    id: "jira-outage",
    label: "Jira outage",
    evidenceLevel: "AUTOMATED TEST",
    title: "Uncertain connector outcomes reconcile before retry.",
    summary:
      "The synthetic connector suite covers pre-send timeout, uncertain acceptance, acknowledgement loss, throttling, server failure, and permission denial without claiming a real Jira write.",
    control: "Idempotency and reconciliation",
    proof: "Connector fault suite; not a live integration",
    href: "https://github.com/TasfiqJ/ResolveFlow/blob/main/tests/integration/test_action_faults.py",
    linkLabel: "Review the fault suite",
  },
] as const;

export default function ScenarioExplorer() {
  const [selectedId, setSelectedId] = useState(scenarios[0].id);
  const tabs = useRef<Array<HTMLButtonElement | null>>([]);
  const selected =
    scenarios.find((scenario) => scenario.id === selectedId) ?? scenarios[0];
  const selectedIndex = scenarios.indexOf(selected);

  const moveTabFocus = (
    event: KeyboardEvent<HTMLButtonElement>,
    currentIndex: number,
  ) => {
    let nextIndex: number | undefined;
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      nextIndex = (currentIndex + 1) % scenarios.length;
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      nextIndex = (currentIndex - 1 + scenarios.length) % scenarios.length;
    } else if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = scenarios.length - 1;
    }
    if (nextIndex === undefined) {
      return;
    }
    event.preventDefault();
    setSelectedId(scenarios[nextIndex].id);
    tabs.current[nextIndex]?.focus();
  };

  return (
    <section className="scenarioExplorer" aria-labelledby="scenario-heading">
      <div className="scenarioExplorerIntro">
        <div>
          <p className="eyebrow">SCENARIO EVIDENCE</p>
          <h2 id="scenario-heading">Know what is recorded—and what is not.</h2>
        </div>
        <p>
          Only two conditions have public snapshots. The remaining controls are
          linked to deterministic tests instead of being presented as
          interactive runs.
        </p>
      </div>
      <div
        className="scenarioTabs"
        role="tablist"
        aria-label="Replay evidence scenarios"
      >
        {scenarios.map((scenario, index) => (
          <button
            aria-controls="scenario-panel"
            aria-selected={scenario.id === selected.id}
            className={scenario.id === selected.id ? "active" : undefined}
            id={`scenario-tab-${scenario.id}`}
            key={scenario.id}
            onClick={() => setSelectedId(scenario.id)}
            onKeyDown={(event) => moveTabFocus(event, index)}
            ref={(element) => {
              tabs.current[index] = element;
            }}
            role="tab"
            tabIndex={index === selectedIndex ? 0 : -1}
            type="button"
          >
            <span>{scenario.label}</span>
            <small>{scenario.evidenceLevel}</small>
          </button>
        ))}
      </div>
      <article
        aria-labelledby={`scenario-tab-${selected.id}`}
        className="scenarioPanel"
        id="scenario-panel"
        role="tabpanel"
        tabIndex={0}
      >
        <div className="scenarioEvidenceLevel">
          <span>{selected.evidenceLevel}</span>
          <small>{selected.proof}</small>
        </div>
        <h3>{selected.title}</h3>
        <p>{selected.summary}</p>
        <dl>
          <div>
            <dt>CONTROL UNDER TEST</dt>
            <dd>{selected.control}</dd>
          </div>
          <div>
            <dt>PUBLIC EVIDENCE</dt>
            <dd>{selected.proof}</dd>
          </div>
        </dl>
        <Link href={selected.href}>{selected.linkLabel} ↗</Link>
      </article>
    </section>
  );
}
