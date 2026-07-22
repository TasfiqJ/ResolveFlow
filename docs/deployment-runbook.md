# Snapshot deployment runbook

## Build

Run `make bootstrap`, `scripts/verify.sh`, then build with `NEXT_PUBLIC_BASE_PATH=/ResolveFlow pnpm --dir apps/web build`. The exported `apps/web/out` directory must pass `uv run python scripts/scan_public_build.py --path apps/web/out --strict` and `uv run python scripts/verify_public_snapshots.py`.

## Public safety

GitHub Pages receives only the static export. Do not configure Cohere, Slack, Jira, database, OAuth, cookie, or connector credentials. `RESOLVEFLOW_PUBLIC_LIVE_MODE` remains false and Jira dispatch remains disabled.

## Outage behavior

The public site has no runtime API dependency. If a locally hosted optional live API is unavailable, visitors remain on the checksummed recorded run and see an explicit live-unavailable message.

## Rollback

Redeploy the previous successful static artifact. Do not rewrite or relabel existing snapshots. Verify the prior artifact with the bundle secret scan and snapshot checksum command before reactivation.
