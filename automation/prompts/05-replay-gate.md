# Stage 05 — Replay and release gate

Read:

- `docs/spec/00_ResolveFlow_Replay_Project_Overview_and_Feature_Catalog.md`
- `docs/spec/10_Feature_10_indirect_prompt_injection_defense.md`
- `docs/spec/13_Feature_13_complete_audit_trace_and_run_diff.md`
- `docs/spec/14_Feature_14_replay_scenario_compiler.md`
- `docs/spec/15_Feature_15_readiness_gate_and_CI_release_decision.md`

Implement:

- versioned base-truth and scenario schemas;
- YAML Replay manifests and typed mutation registry;
- frozen clock, identity, ACL, corpus, policy, connector, and feature-flag state;
- deterministic materialization and dry-run command;
- the same production Resolve path for Replay;
- unsafe-v0 and guarded-v1 configurations;
- paired run comparison;
- hard-invariant-first scoring;
- exact numerators/denominators and uncertainty calculations;
- SHIP, SHIP_WITH_LIMITS, and NO_SHIP logic;
- checksummed machine-readable result bundles;
- GitHub Actions Replay smoke and negative gate tests;
- public Replay and release-result interfaces.

Any Codex-created truth or scenario content must be labeled `DRAFT_PENDING_HUMAN_REVIEW`. Do not call it human-authored, lock held-out data, or fabricate evaluation outcomes. Expand `scripts/verify.sh`, run it, and leave the working tree ready for the outer loop.
