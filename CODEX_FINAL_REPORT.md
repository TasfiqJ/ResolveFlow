# ResolveFlow Replay technical-preview report

**Audit date:** 2026-07-22

**Branch:** `main`

**Release profile:** `technical_preview`

**Rollback target:** `e30f56714dcbc57fc861c1eeb0e2d4dbf3dfa56c`

## Outcome

ResolveFlow Replay is prepared as a zero-cost, snapshot-first technical preview. The implemented product uses one shared Resolve path for interactive and Replay execution, keeps public writes disabled, publishes only synthetic recorded evidence, and identifies missing human validation instead of manufacturing it.

This is not a final deployment-readiness verdict. The validated-release profile remains closed because the repository has 0 human-authored truths, 0 practitioners, 0 reviewed cases, no locked held-out evaluation, and no fluent-language signoff.

## Implemented product

- Nine static routes covering Resolve, Replay, results, architecture, methodology, project context, blinded review tooling, and a recorded audit trace.
- Authorization before retrieval, deterministic context tools, hybrid retrieval boundaries, bounded agent execution, claim-level verification, and hostile-evidence controls.
- Exact-digest approval, disabled real Jira dispatch, idempotent synthetic execution, retry/reconciliation behavior, and append-only audit projection.
- Versioned Replay materialization, shared production-path comparison, hard-invariant-first release decisions, exact-count statistics, and retained failure links.
- Snapshot checksums, public redaction, strict browser-bundle secret scanning, recorded/live provenance, and outage-independent static behavior.

## Measured evidence

The currently published result is one deterministic development-fixture pair:

- unsafe-v0: `NO_SHIP`, with 1 forbidden candidate out of 1 scenario;
- guarded-v1: 0 forbidden candidates out of 1 scenario and 4 verified citations out of 4;
- guarded-v1 verdict: `SHIP_WITH_LIMITS` because citation N=4 is below the draft minimum N=10.

These values are not held-out, live-provider, human-reviewed, or final results.

## Verification

The repository-controlled release checks completed locally on 2026-07-22:

- Python lint, formatting, and mypy passed across 79 source files.
- 134 Python tests, 2 web tests, and 4 PostgreSQL tests passed.
- The migration upgraded, downgraded one revision, and re-upgraded successfully.
- Python and pnpm dependency audits reported no known vulnerabilities. The local package itself is not published on PyPI and was explicitly skipped by `pip-audit`.
- Gitleaks 8.30.1 scanned all 18 reachable commits and found no leaks; the public static bundle scan also passed.
- Replay smoke retained the unsafe failure as `NO_SHIP` and produced the guarded development-fixture result as `SHIP_WITH_LIMITS`.
- Static export with the `/ResolveFlow` base path, all-route snapshot smoke, strict public-claim preflight, and published-snapshot checksum verification passed.
- Digest-pinned database, API, worker, and web images built and started; API live, ready, and version endpoints plus the exported homepage and nested About route returned the expected content.
- An isolated clone of pushed commit `e30f567` completed a frozen install, rebuilt the `/ResolveFlow` export, passed the all-route snapshot smoke, and reproduced the two published artifact hashes. The exact restore record is in `docs/restore-reports/2026-07-22-e30f567.md`.

The Python test run emits one upstream transition warning because Starlette 1.3.1 deprecates its `httpx` TestClient backend in favor of `httpx2`; it does not fail or skip a test.

## External systems and spend

No live Cohere request, real Slack event, real Jira write, paid infrastructure purchase, or billing claim is part of the technical preview. Public mode contains no external write credential. Exact billed spend cannot be queried from the repository; no monetary result is claimed.

## Limitations and next promotion gate

The complete limitation register is in `docs/KNOWN_LIMITATIONS.md`. Promotion to `validated_release` requires genuine human-authored truths, locked gate and held-out artifacts, at least three relevant practitioners across at least ten cases, and either a fluent-human language signoff or continued removal of multilingual quality claims.

## Publication

GitHub Pages publication was observed and verified on 2026-07-22:

- Public URL: [https://tasfiqj.github.io/ResolveFlow/](https://tasfiqj.github.io/ResolveFlow/)
- Successful workflow: [run 29927371263](https://github.com/TasfiqJ/ResolveFlow/actions/runs/29927371263) at commit `9f81f866fe70e7fe453f1b1a670d82c6a3bb9914`
- Build and deploy jobs both completed successfully.
- Homepage and `/about/` returned HTTP 200 with the technical-preview, pending-human-validation, and honest-limitations copy.
- Public hero and Replay snapshots returned HTTP 200 and matched repository SHA-256 values `acfe2a0f...2b80` and `49f5da29...7ac9`.

The exact publication observation is recorded in `docs/deployment-reports/2026-07-22-pages-9f81f86.md`.
