# Common execution contract

You are one stage in a finite, sequential ResolveFlow automation loop.

## Git boundary

- Work only on the existing `main` branch.
- Never create a branch, worktree, pull request, or merge.
- Never commit or push. The outer shell loop owns `git add`, `git commit`, and `git push`.
- Do not reset, discard, or overwrite existing work.
- Uncommitted changes, if present, belong to the current loop attempt. Inspect and preserve them.

Before editing:

1. Run `git branch --show-current` and confirm it is exactly `main`.
2. Run `git status --short`.
3. Read `AGENTS.md`.
4. Read the overview, implementation plan/status files when present, and every feature document named by this stage.

## Work boundary

- Implement only the current stage.
- Use the shared production Resolve path for Resolve and Replay.
- Default to synthetic data, deterministic fixtures, recorded contracts, mocks, and snapshots.
- The loop intentionally withholds `COHERE_API_KEY`; the normal build and test path must not require live Cohere.
- Do not perform real Slack or Jira writes.
- Do not deploy or publish unless this is the explicit publication stage.
- Do not fabricate tests, measurements, costs, reviewer results, provider success, deployment success, or human signoff.
- Make safe reversible implementation decisions and record material ones in `docs/DECISIONS.md`.
- Update `docs/CODEX_STATUS.md` and `docs/ACCEPTANCE_MATRIX.md`.
- Maintain `scripts/verify.sh` as an executable, repository-controlled command that runs every verification check currently required by the implemented scope.

## Completion report

Run all relevant checks before finishing.

Your final response must match the supplied JSON schema.

Use `"status": "complete"` only when the stage is implemented and its relevant tests pass.
Use `"status": "blocked"` for a genuine external or human blocker.
Use `"status": "failed"` when repository-controlled work remains broken.
Set `tests_passed` to `true` only when every required, runnable check passed.
List skipped checks and exact reasons honestly.
