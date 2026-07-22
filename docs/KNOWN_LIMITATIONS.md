# Known limitations

## Release status

This release is a technical preview, not a production-readiness verdict. It publishes automated evidence from deterministic synthetic fixtures and makes no claim of human validation.

## Evidence limits

- The 36 truth candidates are synthetic-agent-authored drafts. Human-authored truth count is 0.
- Practitioner review is incomplete at 0 reviewers and 0 reviewed cases.
- Held-out candidates and final gate rules are not locked, so no held-out or final verdict is available.
- The published comparison contains one deterministic development-fixture pair. Guarded-v1 has 4 verified citations, below the draft reporting minimum of 10.
- The 200-scenario security matrix is deterministic application-control coverage, not 200 independent live-model attacks.
- Automated checks do not constitute an independent security assessment or usability study.

## Integration limits

- No live Cohere run, provider latency, usage, quality, or cost result is claimed.
- Slack handling is verified with signed synthetic contracts; no real workspace result is claimed.
- Jira dispatch is disabled outside the synthetic connector; no real Jira write result is claimed.
- Public mode is static, snapshot-first, English-only, and has no runtime backend or external write credential.

## Scope limits

- One fictional payments workflow and one inert Jira proposal are included.
- Image evidence remains outside the evaluated core.
- The exploratory French fixture is excluded from quality claims because no fluent-human signoff exists.

## Tooling note

- The passing Python suite currently reports one Starlette TestClient deprecation warning while the ecosystem transitions from `httpx` to `httpx2`. No test is skipped or muted.
