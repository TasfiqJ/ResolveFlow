# Stage 08 — prepare zero-cost snapshot-first publication

Run this stage only when the repository-controlled final audit is green, `docs/HUMAN_SIGNOFF.json` permits the selected release profile, and the operator explicitly starts the loop with `RUN_PUBLISH=1`.

Read:

- `CODEX_FINAL_REPORT.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/deployment-runbook.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/spec/18_Feature_18_snapshot_first_public_mode_and_rate_limited_live_mode.md`

Rerun release-critical checks first. If any hard gate or production build fails, repair the repository-controlled problem or report failure; do not prepare publication as successful.

Prepare a zero-cost, snapshot-first static publication through GitHub Pages or another already-authorized configuration that requires no external project spending or billing commitment.

The public build must:

- work without Cohere;
- use synthetic data only;
- expose no external write connector;
- contain no Cohere, Slack, Jira, database, or session secret;
- clearly label recorded snapshots;
- link to repository, method, architecture, results, and limitations;
- publish only measured results with exact denominators;
- include the immutable commit identifier;
- keep live mode disabled unless separately validated and authorized.

For `technical_preview`, the public build must also identify itself as a technical preview, state that human validation is pending, and avoid any final deployment-readiness verdict.

Update README and release documentation with exact reproduction and post-push verification steps. Do not claim a live deployment until it is externally verified. Maintain and run `scripts/verify.sh`; leave the working tree ready for the outer loop to commit and push.
