# ResolveFlow Replay - Codex Instructions

## Required reading

For every task:

1. Read `docs/spec/00_ResolveFlow_Replay_Project_Overview_and_Feature_Catalog.md`.
2. Read `docs/CODEX_MASTER_PROMPT_ResolveFlow.md`.
3. Read `docs/IMPLEMENTATION_PLAN.md` when it exists.
4. Read every feature document named in the current task.

## Working rules

- Work only on the milestone named in the current task.
- Inspect the repository and git status before changing files.
- Preserve existing work.
- Use one shared production path for Resolve and Replay.
- Use synthetic connectors, recorded fixtures, mocks, and snapshots by default.
- Never fabricate tests, measurements, costs, reviewer results, provider success, deployment success, or integration success.
- Never commit secrets, API keys, credentials, tokens, or real customer data.
- Never create paid infrastructure.
- Never perform a real Slack or Jira write unless the task explicitly authorizes it.
- Public mode must have no Slack or Jira write credential.
- Run the relevant tests before declaring a milestone complete.
- Update `docs/CODEX_STATUS.md` and `docs/ACCEPTANCE_MATRIX.md` after every milestone.
- Do not start a later milestone early.
- Do not push, merge, deploy, or publish unless the current task explicitly authorizes it.

## Handling uncertainty

Do not ask routine questions.

Make the safest reversible assumption and record it in `docs/DECISIONS.md`.

Stop and record a blocker before:

- spending money;
- destructive operations;
- credential changes;
- real external writes;
- changing held-out evaluation data after lock;
- publishing unsupported claims.
