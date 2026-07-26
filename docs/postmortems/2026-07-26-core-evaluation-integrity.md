# Unobserved controls were counted as zero failures

**Date:** 2026-07-26

**Affected artifact:** deterministic guarded-v1 development comparison
**Verdict effect:** `SHIP_WITH_LIMITS` under gate 1.0 became `NO_SHIP` under gate 1.1

## Expected behavior

A hard release invariant passes only when the selected evaluation actually observes the relevant
system boundary. Missing evidence, an unexecuted connector path, an unlocked dataset, or an
unchecked deployment configuration must not be represented as zero failures.

## Actual behavior

The role-downgrade Replay exercised authorization, retrieval, the agent/verifier path, and inert
proposal creation. The scorer nevertheless emitted passing zero-failure observations for payload
mismatch and duplicate action using literal constants. It treated the manifest's
`external_writes: false` value as evidence about a deployed public environment and did not fail the
development decision for an unlocked held-out catalog. The audit-chain check followed stored hash
references without recomputing event hashes.

The dataset audit found a second issue: 36 truth IDs share one semantic payload. The 200-cell
security matrix expands identifiers but records zero full Replay executions.

## Root cause

The metric schema had no representation for `not_exercised` or `not_verified`. Every metric
required a positive denominator, which encouraged absent evidence to be encoded as `0/1`. Tests
proved verdict branching with seeded metric values but did not require each passing invariant to
name an observed source boundary. Dataset tests asserted identifier counts, not semantic
distinctness or executable coverage.

## Operator impact

The prior guarded result looked closer to a deployable decision than its evidence justified. A
senior reviewer could reasonably conclude that the gate was validating its own fixtures rather
than enforcing an evidence contract.

## Correction

- Metric observations now carry `observed`, `not_exercised`, or `not_verified` evidence status
  plus a specific note.
- Any non-observed hard invariant is release-blocking.
- Gate 1.1 adds dataset integrity as a hard invariant.
- Audit-event hashes are published and independently recomputed by the scorer.
- A checksummed evaluation-integrity artifact reports semantic truth count, duplicate groups,
  declared versus executed matrix coverage, payload-family coverage, held-out lock state, and
  human-review count.
- The five stored attack payloads are now actually executed through their expected deterministic
  forbidden-effect controls, without relabeling those checks as full Replay executions.
- Live runtime composition now switches Chat, Embed, and Rerank together, applies configured
  models and budgets, and derives recorded/live provenance from the active provider.
- The public candidate verdict and documentation now say `NO_SHIP`.

## Regression protection

`tests/unit/evaluation/test_evidence_backed_scoring.py` prevents unexercised action and deployment
controls from being credited as passes and proves that a modified event with its old hash fails the
audit invariant. `tests/unit/evaluation/test_integrity_audit.py` prevents duplicate truth IDs or a
declared-only security matrix from being presented as independent execution evidence.

## Remaining work

Gate 1.1 should remain `NO_SHIP` until distinct reviewed truths exist, the action lifecycle is
included in compatible Replay scenarios, deployment credential absence is independently attested,
and a held-out lock predates evaluation. This postmortem does not substitute for those results.
