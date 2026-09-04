# Technical-preview release checklist

**Scope:** This checklist records the previously deployed technical-preview
checkpoint. It does not claim that the 2026-09-04 Cohere-focused working-tree
revision is deployed. That revision is locally built and verified but remains
unpublished; the hosted Pages URL currently serves the older preview.

Before any future publication, claim review must preserve hard provider-call,
agent-round, and tool-call caps while describing `max_total_tokens` as a
preflight/post-response observed-usage soft stop and request/wall-clock timeout
as cooperative per-operation handling. Neither control is a hard billing or
total-runtime ceiling without new provider/runtime evidence.

## Release profile

- [x] Operator explicitly authorized the technical preview.
- [x] Human validation is recorded as pending, not complete.
- [x] A final production-release verdict is not claimed.
- [x] Multilingual quality claims are removed.
- [x] Public data is synthetic and public writes remain disabled.

## Repository-controlled audit

- [x] Complete `scripts/verify.sh` passes on the release worktree.
- [x] Strict preflight passes.
- [x] Static production build succeeds with the `/ResolveFlow` base path.
- [x] Public bundle secret scan and snapshot checksum verification pass.
- [x] Browser smoke covers all exported routes.
- [x] Real Chromium journeys cover core navigation, Replay interaction, keyboard skip navigation, WCAG A/AA rules, and mobile overflow.
- [x] GitHub Actions are pinned to full commit SHAs and Pages deployment depends on repository gates and strict preflight.
- [x] PostgreSQL migration upgrade, downgrade, re-upgrade, and database tests pass.
- [x] Release documentation, license, source notes, limitations, rollback, and postmortem are complete.
- [x] Isolated clean clone restores the Pages build and checksummed snapshot experience.
- [x] Local `main` and `origin/main` matched at that prior release checkpoint.

## Prior publication checkpoint

- [x] GitHub Pages workflow completes successfully.
- [x] The public URL returns the technical-preview homepage.
- [x] At least one nested route and both checksummed snapshots are reachable.
- [x] No live provider, Slack, Jira, database, session, or write credential is present.
- [x] The observed deployment URL and workflow result are added to the final report.

Unchecked items are pending measurements, not implied successes.
