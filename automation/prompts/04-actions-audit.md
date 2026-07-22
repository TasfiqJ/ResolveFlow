# Stage 04 — actions, reliability, and audit

Read:

- `docs/spec/00_ResolveFlow_Replay_Project_Overview_and_Feature_Catalog.md`
- `docs/spec/11_Feature_11_approval_gated_Jira_proposal.md`
- `docs/spec/12_Feature_12_idempotent_connector_execution_and_recovery.md`
- `docs/spec/13_Feature_13_complete_audit_trace_and_run_diff.md`

Implement:

- inert Jira proposals created only from verified evidence;
- canonical payload digest;
- approval, rejection, expiry, invalidation, and permission states;
- durable PostgreSQL jobs and transactional claiming;
- leases, retries, bounded backoff, dead letters, and safe reclaim;
- uncertain-send reconciliation and one idempotency key per logical action;
- synthetic Jira connector and disabled-by-default real adapter;
- append-only audit events committed with critical state changes;
- full trace timeline, deterministic public redaction, export, and diff foundation;
- approval/action UI;
- forced timeout, crash, duplicate-dispatch, concurrency, and redaction tests.

No real Jira write may occur. Expand `scripts/verify.sh`, run it, and leave the working tree ready for the outer loop.
