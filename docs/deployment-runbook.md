# Snapshot deployment runbook

## Deployment profile

Publish only the `technical_preview` profile authorized by `docs/HUMAN_SIGNOFF.json`. The public product may show deterministic fixture results, but it must not claim human validation, held-out evidence, or a final production-release verdict.

## Build

Run `make bootstrap`, `scripts/verify.sh`, then build with `NEXT_PUBLIC_BASE_PATH=/ResolveFlow pnpm --dir apps/web build`. The exported `apps/web/out` directory must pass `uv run python scripts/scan_public_build.py --path apps/web/out --strict` and `uv run python scripts/verify_public_snapshots.py`.

## Public safety

GitHub Pages receives only the static export. Do not configure Cohere, Slack, Jira, database, OAuth, cookie, or connector credentials. `RESOLVEFLOW_PUBLIC_LIVE_MODE` remains false and Jira dispatch remains disabled.

## Outage behavior

The public site has no runtime API dependency. If a locally hosted optional live API is unavailable, visitors remain on the checksummed recorded run and see an explicit live-unavailable message.

## Rollback

The pre-audit rollback target is commit `724f53c9a5aee3b90da339e5717e6b5cb767bc81`. Redeploy that immutable source or the previous successful Pages artifact. Do not rewrite or relabel existing snapshots. Verify the prior artifact with the bundle secret scan and snapshot checksum command before reactivation.

## Credential and publication shutdown

GitHub Pages receives no application secret. To stop publication, disable the Pages environment or deploy the verified rollback target. If a future private environment adds provider or connector credentials, disable dispatch first, revoke the credential at its provider, remove the hosted value, reconcile uncertain actions, and retain the sanitized audit record.

## Archive

Archive the release commit, public snapshots and checksum files, result bundle, generated report, release checklist, known limitations, workflow run reference, and observed public URL. Never archive `.env` files, tokens, private reviewer exports, unrestricted traces, or real connector payloads in the public repository.
