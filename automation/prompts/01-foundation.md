# Stage 01 — foundation vertical slice

Read:

- `docs/spec/00_ResolveFlow_Replay_Project_Overview_and_Feature_Catalog.md`
- `docs/spec/01_Feature_01_Slack_style_intake_and_real_Slack_sandbox.md`
- `docs/spec/02_Feature_02_deterministic_context_enrichment.md`
- `docs/spec/07_Feature_07_bounded_Command_A_agent_loop.md`
- `docs/spec/13_Feature_13_complete_audit_trace_and_run_diff.md`
- `docs/spec/18_Feature_18_snapshot_first_public_mode_and_rate_limited_live_mode.md`

Implement the smallest complete vertical slice:

- repository/application scaffold;
- Next.js application shell;
- FastAPI application;
- PostgreSQL development setup and migrations;
- worker skeleton;
- Docker Compose local environment;
- one canonical synthetic payments incident;
- web-created canonical case;
- deterministic context enrichment;
- one fixture-backed cited Resolve result;
- minimal chronological trace;
- snapshot-first public demo;
- health and version endpoints;
- static, unit, integration, and basic browser tests;
- setup and development documentation.

Do not require a Cohere key. Do not complete future retrieval, verifier, Jira, Replay, or release-gate scope yet; provide typed interfaces for those boundaries. Expand `scripts/verify.sh`, run it, and leave the working tree ready for the outer loop.
