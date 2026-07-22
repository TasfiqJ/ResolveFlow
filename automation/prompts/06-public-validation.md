# Stage 06 — public product and validation tooling

Read:

- `docs/spec/00_ResolveFlow_Replay_Project_Overview_and_Feature_Catalog.md`
- `docs/spec/01_Feature_01_Slack_style_intake_and_real_Slack_sandbox.md`
- `docs/spec/11_Feature_11_approval_gated_Jira_proposal.md`
- `docs/spec/16_Feature_16_human_review_and_practitioner_scoring.md`
- `docs/spec/17_Feature_17_one_validated_multilingual_slice.md`
- `docs/spec/18_Feature_18_snapshot_first_public_mode_and_rate_limited_live_mode.md`

Implement:

- complete public route set;
- polished snapshot-first hero workflow;
- case, evidence, response, action, trace, Replay, comparison, scorecard, architecture, methodology, and about views;
- checksummed stored result snapshots and unmistakable recorded/live labels;
- predefined live inputs, server-side quotas, one-run concurrency, timeout, queue, and kill switch;
- browser-bundle secret scan and graceful outage fallback;
- Slack adapter and signature-verification code;
- Jira staging adapter configuration;
- blinded randomized human-review application;
- exact-count export and analysis commands;
- multilingual fixture and signoff structure.

Do not invent reviewer responses, claim a validated language without fluent-human signoff, perform real Slack/Jira writes, or enable public live mode. Expand `scripts/verify.sh`, run it, and leave the working tree ready for the outer loop.
