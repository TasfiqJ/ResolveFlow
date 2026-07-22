# Stage 00 — executable implementation plan

Read completely:

- `docs/CODEX_MASTER_PROMPT_ResolveFlow.md`
- `docs/spec/00_ResolveFlow_Replay_Project_Overview_and_Feature_Catalog.md`
- every feature document under `docs/spec/`
- `docs/reference/ResolveFlow_Replay_Master_Plan.pdf`
- the complete existing repository, tests, configuration, scripts, and git history

Do not implement product behavior in this stage.

Create or complete:

1. `docs/IMPLEMENTATION_PLAN.md`
2. `docs/ACCEPTANCE_MATRIX.md`
3. `docs/CODEX_STATUS.md`
4. `docs/DECISIONS.md`
5. necessary ADRs under `docs/adr/`
6. executable `scripts/verify.sh`

The plan must define:

- architecture and repository structure;
- shared domain schemas, state machines, module boundaries, APIs, and migration ownership;
- exact dependency-safe milestone order;
- every acceptance criterion mapped to an automated test or explicit human evidence item;
- exact setup, lint, type-check, unit, integration, browser, security, Replay, and release commands;
- credential-dependent, external-account, and human-only work;
- zero-cost snapshot/fixture defaults;
- implementation-time facts that must be measured rather than guessed;
- a rollback and migration policy;
- how `scripts/verify.sh` expands as the repository grows.

Review the result against all nineteen specification documents. Commit nothing and push nothing.
