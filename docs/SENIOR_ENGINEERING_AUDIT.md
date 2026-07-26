# Senior engineering audit

**Audit date:** 2026-07-26

**Verdict:** The architecture is resume-impressive; the evaluation evidence is not yet
production-impressive.

ResolveFlow is materially stronger than a normal portfolio agent demo. It has an explicit threat
model, authorization before retrieval, bounded tools, claim-level verification, exact approval
digests, retry/reconciliation models, a shared Resolve/Replay path, deterministic snapshots,
release gates, migrations, browser tests, and failure artifacts. That breadth shows strong systems
judgment.

The original project nevertheless had a credibility problem. It looked more evaluated than it
was. A skeptical senior engineer could find counters and passing gates that were not backed by
executions at the boundary they claimed to measure. The corrected project is more impressive
because it now detects and blocks its own unsupported claims.

## Highest-severity findings

### 1. The release gate rewarded missing evidence

Gate 1.0 emitted passing `0/1` values for payload mismatch and duplicate action even though the
published Replay never dispatched an action. It inferred public credential safety from a scenario
manifest and did not block an unlocked held-out set.

Gate 1.1 gives every hard observation an evidence state: `observed`, `not_exercised`, or
`not_verified`. Anything other than observed is release-blocking. The guarded build is therefore
`NO_SHIP`, which is the only defensible result.

### 2. Thirty-six truth IDs represented one case

A canonical fingerprint over timeline, domain, evidence inventory, answerability, route, unknowns,
action, and expected mutation behavior shows 36 IDs collapsing to 1 semantic truth template.
Unique identifiers are not independent evaluation cases.

The checksummed dataset audit makes that fact machine-readable and gate 1.1 treats failed
distinctness as a hard failure. Fixing the number would require genuine distinct truth authoring
and review; generating cosmetic variants would repeat the original mistake.

### 3. The 200-scenario claim was a Cartesian declaration

The security matrix expands to 200 unique IDs, but it has 0 checksummed full Replay executions and
only 5 unique payloads for 20 family/variant slots. The old count test proved arithmetic, not
security coverage.

The public evidence now says `0/200`. All 5 stored attack payloads do execute their expected
deterministic forbidden-effect controls, but that result is kept separate from full Replay or
live-model evidence.

### 4. The live-provider path was internally inconsistent

The API could select Cohere Chat while retrieval silently retained fixture Embed and Rerank
adapters. Configured Command and Embed model settings and agent budgets were not fully applied.
A non-fixture query vector could also be compared with incompatible stored fixture vectors.

One composition root now switches Chat, Embed, and Rerank together. When the configured embedding
model is absent from the frozen corpus, document vectors are computed only after snapshot and ACL
filtering. Contract coverage proves restricted legal content is not sent to the embedder and that
authorized document vectors are cached separately from query results.

### 5. Provenance and audit integrity were weaker than advertised

`RunSnapshot` structurally labeled every run `recorded_fixture`, including a potential live run.
Published trace typing dropped event hashes, and the scorer followed stored links without
recomputing hashes.

Provenance is now derived from the active provider. Public snapshots retain the hash chain, and
the scorer independently recomputes each event hash and link. A tamper regression changes event
content while retaining its old hash and correctly blocks the invariant.

## What a senior reviewer should still challenge

- There is one published paired Replay, not a meaningful evaluation distribution.
- The guarded role-downgrade Replay exercises 5 of 10 hard invariants. Action lifecycle,
  deployment credential, and held-out integrity evidence remain absent or unverified.
- There are 0 human-authored truths, 0 practitioner reviewers, and 0 reviewed cases.
- No live Cohere result exists for quality, latency, usage, failure rate, or cost.
- The public-live limiter is implemented, but no bounded persistent live executor exists. The API
  now returns an explicit executor-unavailable fallback instead of accepting ghost queued work.
- Slack and Jira evidence is synthetic. No authorized development tenant result exists.
- API action, Replay, and Slack stores are process-local memory. Durable PostgreSQL repositories
  and worker behavior are implemented and tested separately but are not the current API
  composition.
- The public product covers one fictional payments workflow. Generality is architectural, not
  empirically demonstrated.
- No independent security assessment, usability study, fluent-language review, or observed
  production operation exists.

These are not polish tasks. They require new evidence, genuine reviewers, authorized external
systems, or a larger runtime integration milestone.

## Resume framing

Defensible:

> Built a deterministic Replay and fail-closed release-gate system for an enterprise agent
> prototype, including authorization-before-retrieval, claim-level verification, exact approval
> boundaries, fault injection, evidence-status-aware hard gates, semantic dataset audits, and
> tamper-detecting snapshots.

Not defensible yet:

- production-ready or production-proven;
- evaluated on 36 independent truths;
- tested across 200 executed security Replays;
- validated with live Cohere, Slack, or Jira;
- human-validated or held-out performance;
- exactly-once behavior proven in a real external connector.

## Bottom line

Before this audit, the project was visually and architecturally impressive but vulnerable to a
senior reviewer calling parts of the evaluation “metric theater.” After the audit, the strongest
feature is the evidence contract itself: unsupported success is converted into a visible,
machine-readable `NO_SHIP`. That is credible senior-level judgment. The next step is not more UI;
it is accumulating real, distinct, independently reviewed executions without weakening the gate.
