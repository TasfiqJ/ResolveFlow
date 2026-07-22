# Stage 07 — final definition-of-done audit and repair

The outer loop runs this stage only after `docs/HUMAN_SIGNOFF.json` passes its human gate.

Read:

- `docs/CODEX_MASTER_PROMPT_ResolveFlow.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/ACCEPTANCE_MATRIX.md`
- `docs/CODEX_STATUS.md`
- `docs/DECISIONS.md`
- `docs/HUMAN_SIGNOFF.json`
- every document under `docs/spec/`
- `docs/reference/ResolveFlow_Replay_Master_Plan.pdf`
- the complete implementation and git history

For every acceptance criterion, identify the implementation and evidence, run the relevant command, repair repository-controlled defects, and mark external/human limitations honestly.

Run and repair as applicable:

- formatting and lint;
- Python and TypeScript type checks;
- unit, database integration, contract, and browser tests;
- authorization/security, concurrency, connector-failure, Replay, and negative release-gate tests;
- accessibility and secret scans;
- production builds and Docker startup checks.

Verify specifically:

- no forbidden evidence enters retrieval or output;
- no model-triggered external write exists;
- approval binds the exact digest;
- retries create no duplicate effect;
- Replay uses the production Resolve path;
- public output is deterministically redacted;
- snapshots and live output are distinct;
- no fabricated result, reviewer evidence, provider success, or deployment claim exists;
- public production contains no Slack or Jira write credential.

Create or update:

- `CODEX_FINAL_REPORT.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/THREAT_MODEL.md`
- `docs/DEPLOYMENT_RUNBOOK.md`
- one genuine failed-case postmortem when evidence exists

Expand `scripts/verify.sh` into the complete release-critical verifier, run it, and leave the working tree ready for the outer loop.
