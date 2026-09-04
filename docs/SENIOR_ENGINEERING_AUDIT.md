# Senior engineering audit

**Audit date:** 2026-07-26

**Evidence update:** 2026-08-14. The original findings remain as historical audit context; the
live Cohere evidence boundary below reflects the subsequently published artifacts.

**Verdict:** The architecture is resume-impressive; the evaluation evidence is not yet
production-impressive.

ResolveFlow is materially stronger than a normal portfolio agent demo. It has an explicit threat
model, authorization before retrieval, bounded tools, claim-level verification, payload-digest
approval checks, retry/reconciliation models, a shared Resolve/Replay path, deterministic
snapshots, release gates, migrations, browser tests, and failure artifacts. Those approval checks
bind proposal state and payload exactly, but the local API does not authenticate callers; actor
identity and permission scopes must come from a trusted upstream layer. That breadth shows strong
systems judgment.

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

The security matrix expands to 200 unique IDs. A later remediation executed every cell through the
guarded-v1 recorded-fixture production path and retained manifest, materialization, run, final-trace,
and per-cell result hashes. The 2026-08-12 snapshot records 200 passes and 0 open cell failures.

The public evidence now says `200/200 executed`, `200 passed`, and `0 open issues`. That fixes the
execution-evidence gap but not attack diversity: all matrix cells reference one stored hostile
artifact across 20 family/variant labels, and none is a live-model attack. The separate five-payload
detector suite remains reported separately.

### 4. The live-provider path was internally inconsistent

The API could select Cohere Chat while retrieval silently retained fixture Embed and Rerank
adapters. Configured Command and Embed model settings and agent budgets were not fully applied.
A non-fixture query vector could also be compared with incompatible stored fixture vectors.

One composition root now switches Chat, Embed, and Rerank together. When the configured embedding
model is absent from the frozen corpus, document vectors are computed only after snapshot and ACL
filtering. Contract coverage proves restricted legal content is not sent to the embedder and that
authorized document vectors are cached separately from query results. A later live A/B exercised
the composed Command A+ and Rerank v4 path while reusing a cache from an earlier Embed v4 pass.

### 5. Provenance and audit integrity were weaker than advertised

`RunSnapshot` structurally labeled every run `recorded_fixture`, including a potential live run.
Published trace typing dropped event hashes, and the scorer followed stored links without
recomputing hashes.

Provenance is now derived from the active provider. Public snapshots retain the hash chain, and
the scorer independently recomputes each event hash and link. A tamper regression changes event
content while retaining its old hash and correctly blocks the invariant.

### 6. Live execution exists, but the quality result is void

The fixed call/round-policy live Cohere A/B contains one coherent 32-run repetition, 16 runs per build. Its
reconciled ledger records 197 Chat calls and 36 Rerank calls, 233 provider calls in total with no
retries: 206 for the selected full pass and 27 for its dry pass. Low completion -- 1/16 for
guarded-v1 and 3/16 for unsafe-v0 -- voids citation precision, route accuracy, and completion rate
as quality metrics. Offline recovery excluded 63 snapshots from other execution timestamps rather
than publishing a mixed cohort, and spent zero provider calls. The execution git state was
`uncommitted`; its exact dirty diff was not retained.

The defensible result occurs before model completion: unsafe-v0 retrieved forbidden evidence in
16/16 runs and guarded-v1 in 0/16. The guarded-minus-unsafe difference is -100 percentage points
with a descriptive Newcombe hybrid-score 95% interval of [-100, -72.6197], excluding zero. A later reduced
11-scenario completion-budget follow-up consumed 161 attempts, including 27 retries, and still
completed 0/11 guarded runs. It is diagnostic evidence of the next constraints, not a successful
quality rerun. Neither live artifact records an external write or supports a monetary-cost,
held-out, human-validation, production, or final-release claim.

## What a senior reviewer should still challenge

- There is one published paired Replay, not a meaningful evaluation distribution.
- The guarded role-downgrade Replay exercises 5 of 10 hard invariants. Action lifecycle,
  deployment credential, and held-out integrity evidence remain absent or unverified.
- There are 0 human-authored truths, 0 practitioner reviewers, and 0 reviewed cases.
- Live Cohere call, token, timing, and terminal-state telemetry exists for the published synthetic
  runs. The low-completion A/B supports no model-quality result, the follow-up did not improve
  guarded completion, and neither artifact supports an SLO, monetary-cost, or production claim.
- Only provider-call, agent-round, and tool-call counts are hard admission caps. The total-token
  threshold is checked from observed usage after responses, and deadline enforcement is
  cooperative per operation with a post-return elapsed-time check; neither is a hard billing or
  end-to-end runtime ceiling.
- The public-live limiter is implemented, but no bounded persistent live executor exists. The API
  now returns an explicit executor-unavailable fallback instead of accepting ghost queued work.
- Slack and Jira evidence is synthetic. No authorized development tenant result exists.
- API action, Replay, and Slack stores are process-local memory. Durable PostgreSQL repositories
  and worker behavior are implemented and tested separately but are not the current API
  composition.
- The local action API trusts caller-supplied actor IDs and permission scopes. Its exact
  payload-digest and state checks are not an end-to-end human identity guarantee without a trusted
  upstream authentication and authorization layer.
- The public product covers one fictional payments workflow. Generality is architectural, not
  empirically demonstrated.
- No independent security assessment, usability study, fluent-language review, or observed
  production operation exists.

These are not polish tasks. They require new evidence, genuine reviewers, authorized external
systems, or a larger runtime integration milestone.

## Resume framing

Defensible:

> Built a deterministic Replay and fail-closed release-gate system for an enterprise agent
> prototype, including authorization-before-retrieval, claim-level verification, a payload-digest
> approval state machine with an explicit trusted-identity assumption, fault injection,
> evidence-status-aware hard gates, semantic dataset audits, and tamper-detecting snapshots.

Not defensible yet:

- production-ready or production-proven;
- evaluated on 36 independent truths;
- tested across 200 diverse or live-model security Replays (the 200 executed cells reuse one
  hostile payload and the recorded-fixture path);
- validated for Cohere quality or robustness, or validated with live Slack or Jira;
- human-validated or held-out performance;
- exactly-once behavior proven in a real external connector.

## Bottom line

Before this audit, the project was visually and architecturally impressive but vulnerable to a
senior reviewer calling parts of the evaluation “metric theater.” After the audit, the strongest
feature is the evidence contract itself: unsupported success is converted into a visible,
machine-readable `NO_SHIP`. That is credible senior-level judgment. The next step is not more UI;
it is accumulating real, distinct, independently reviewed executions without weakening the gate.
