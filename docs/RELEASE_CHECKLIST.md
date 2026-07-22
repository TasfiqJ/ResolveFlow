# Technical-preview release checklist

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
- [x] PostgreSQL migration upgrade, downgrade, re-upgrade, and database tests pass.
- [x] Release documentation, license, source notes, limitations, rollback, and postmortem are complete.
- [x] Isolated clean clone restores the Pages build and checksummed snapshot experience.
- [x] Local `main` and `origin/main` match after the release push.

## Publication

- [ ] GitHub Pages workflow completes successfully.
- [ ] The public URL returns the technical-preview homepage.
- [ ] At least one nested route and one checksummed snapshot are reachable.
- [ ] No live provider, Slack, Jira, database, session, or write credential is present.
- [ ] The observed deployment URL and workflow result are added to the final report.

Unchecked items are pending measurements, not implied successes.
