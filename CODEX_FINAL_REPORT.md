# ResolveFlow Replay core-audit report

**Audit date:** 2026-07-26

**Branch:** `main`

**Source state:** revision containing this report

**Release profile:** `technical_preview`

## Outcome

ResolveFlow remains an impressive systems prototype, but it is not a validated release. The
current checksummed development result is intentionally fail closed:

- unsafe-v0: `NO_SHIP`, including one forbidden candidate in one scenario;
- guarded-v1: `NO_SHIP`;
- guarded-v1 hard evidence: 5 of 10 hard invariants observed;
- semantic truth evidence: 1 unique template across 36 draft IDs;
- security-matrix evidence: 200 of 200 cells executed as recorded-fixture Replays, with 200 passes and 0 open cell issues;
- stored attack controls: 5 of 5 payloads exercise their expected deterministic controls.

The guarded build fixes the demonstrated role-downgrade authorization failure. It is still blocked
by unexercised action invariants, unverified public credential state, an unlocked held-out set,
failed dataset distinctness, and insufficient citation sample size.

This is not a final, held-out, live-provider, human-reviewed, connector-backed, or
production-readiness verdict.

## Core corrections

- Gate 1.1 distinguishes observed evidence from `not_exercised` and `not_verified` evidence and
  blocks every missing hard invariant.
- A checksummed integrity artifact fingerprints truth semantics, exposes duplicate truth groups,
  separates declared matrix cells from executed Replays, and records exact human-review/lock
  state.
- The five stored attack payloads are executed through their expected deterministic
  forbidden-effect controls without being mislabeled as 200 Replay results.
- Public snapshots retain audit hashes, and scoring recomputes every event hash and chain link.
- Live runtime composition switches Chat, Embed, and Rerank together, applies configured
  models/budgets, and derives snapshot provenance from the active provider.
- Non-fixture document embeddings are computed only over snapshot-current, ACL-authorized
  candidates; restricted content exclusion is contract-tested.
- Public-live admission no longer returns a queued ticket without an executor; it fails closed
  with the recorded fallback.
- Public Results and Audit pages now present the fail-closed verdict and the exact 1/36,
  200/200-executed, 200-passed/0-open, and 5/5 evidence boundaries.

## Verification performed for this source state

- Ruff lint and format checks: passed.
- Mypy strict checking: passed across 81 source files.
- Python unit, integration, contract, security, and Replay suites: 144 passed; one documented
  Starlette TestClient transition warning.
- Web lint, formatting, and TypeScript: passed.
- Web component suite: 3 passed.
- GitHub Pages-prefixed static build: passed, 12 pages generated.
- Static route smoke: passed.
- Chromium Playwright/Axe suite: 9 passed, including nested navigation, Replay interaction,
  keyboard behavior, WCAG A/AA scans, and mobile overflow.
- Public bundle secret scan, snapshot integrity, and strict technical-preview preflight: passed.
- Replay smoke and seeded unsafe negative gate: passed.
- Published dataset-integrity artifact reproduced byte-for-byte.

No successful GitHub Actions run, clean-clone restore, container startup, PostgreSQL migration
cycle, dependency audit, live provider call, external connector write, human review, or deployment
is claimed for this source state. Earlier dated reports remain historical evidence for their
recorded commits only.

## Remaining promotion blockers

1. Author genuinely distinct cases and obtain qualified human review.
2. Pre-register and lock the held-out set and gate before evaluation.
3. Add compatible Replay scenarios that execute approval, dispatch, timeout, reconciliation,
   payload mismatch, and duplicate-effect boundaries.
4. Independently attest public deployment credentials and runtime configuration.
5. Implement a durable bounded live executor, then run an authorized provider evaluation and
   retain latency, usage, error, quality, and cost evidence.
6. Wire durable repositories into the API runtime or explicitly keep it a fixture service.
7. Exercise Slack/Jira only in explicitly authorized non-production tenants.
8. Obtain independent security and usability review before any production claim.

## External systems and spend

No Cohere key, Slack credential, Jira credential, real customer data, paid infrastructure, or
external write was used. No cost or provider-success claim is made.
