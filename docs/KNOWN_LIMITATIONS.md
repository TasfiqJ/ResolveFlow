# Known limitations

## Release status

This release is a technical preview, not a production-readiness verdict. It publishes automated evidence from deterministic synthetic fixtures and makes no claim of human validation.

## Evidence limits

- The 36 truth-catalog IDs are synthetic-agent-authored drafts, and the integrity audit shows they collapse to 1 unique semantic template. They are scaffolding, not 36 independent cases. Human-authored truth count is 0.
- Practitioner review is incomplete at 0 reviewers and 0 reviewed cases.
- Held-out candidates and final gate rules are not locked, so no held-out or final verdict is available.
- The published comparison contains one deterministic development-fixture pair. Guarded-v1 has 4 verified citations, below the draft reporting minimum of 10.
- Only the role-downgrade comparison and its baseline have public recorded snapshots. The other Replay explorer cases link to automated test evidence and are not presented as recorded or live runs.
- The security matrix declares 200 Cartesian cells, but 0 are currently materialized and executed as full Replay runs. It contains 5 unique attack payloads for 20 declared family/variant slots. All 5 stored payloads exercise their expected deterministic forbidden-effect controls, but that bounded scanner evidence is not a full Replay or live-model result.
- The published paired Replay stops at an inert proposal. Unapproved-write, payload-mismatch, duplicate-action, and deployment-credential hard gates are therefore unexercised or unverified in that result and are release-blocking under gate 1.1.
- Automated checks do not constitute an independent security assessment or usability study.

## Integration limits

- No live Cohere run, provider latency, usage, quality, or cost result is claimed.
- The optional public-live admission endpoint fails closed with
  `public_live_executor_unavailable`; limiter controls exist, but no ticket is accepted until a
  bounded persistent executor is implemented.
- Slack handling is verified with signed synthetic contracts; no real workspace result is claimed.
- Jira dispatch is disabled outside the synthetic connector; no real Jira write result is claimed.
- Fixture API action, Replay, and Slack state is process-local memory. Durable PostgreSQL action repositories and worker behavior are separately implemented and tested, but they are not the current API runtime composition.
- Public mode is static, snapshot-first, English-only, and has no runtime backend or external write credential.

## Scope limits

- One fictional payments workflow and one inert Jira proposal are included.
- Image evidence remains outside the evaluated core.
- The exploratory French fixture is excluded from quality claims because no fluent-human signoff exists.

## Tooling note

- The passing Python suite currently reports one Starlette TestClient deprecation warning while the ecosystem transitions from `httpx` to `httpx2`. No test is skipped or muted.
- Production JavaScript dependencies pass a high-severity audit. The ESLint 9 development toolchain still contains one high-severity transitive `brace-expansion` advisory through `eslint-plugin-import`/`minimatch` 3; forcing the patched major globally breaks that plugin stack, and ESLint 10 is not yet supported by the installed React/import accessibility plugins. The verifier therefore fails on high production findings and critical development findings while this explicit development-only exception remains open.
