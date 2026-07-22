# ResolveFlow Replay Markdown document set

This package contains the complete ResolveFlow Replay project blueprint and eighteen standalone feature specifications, converted from the approved DOCX document set into GitHub-Flavored Markdown.

The original master plan is 87 pages. The document set preserves its core product thesis, scope boundaries, architecture, security model, release-gate design, implementation roadmap, acceptance criteria, and no-guesswork separation between verified facts, design decisions, project gates, and implementation-time facts.

## Reading order

Start with Document 00. Then use the feature documents in dependency and roadmap order: 01-02, 03-06, 07-10, 11-12, 13-15, 16-17, and 18.

## Documents

1. [00 — Project overview and feature catalog](00_ResolveFlow_Replay_Project_Overview_and_Feature_Catalog.md)
2. [01 — Slack-style intake and real Slack sandbox](01_Feature_01_Slack_style_intake_and_real_Slack_sandbox.md)
3. [02 — Deterministic context enrichment](02_Feature_02_deterministic_context_enrichment.md)
4. [03 — Corpus ingestion, versioning, and effective time](03_Feature_03_corpus_ingestion_versioning_and_effective_time.md)
5. [04 — Pre-retrieval authorization and role switch](04_Feature_04_pre_retrieval_authorization_and_role_switch.md)
6. [05 — Hybrid retrieval with Embed v4](05_Feature_05_hybrid_retrieval_with_Embed_v4.md)
7. [06 — Rerank v4 Fast-Pro decision policy](06_Feature_06_Rerank_v4_Fast_Pro_decision_policy.md)
8. [07 — Bounded Command A+ agent loop](07_Feature_07_bounded_Command_A_agent_loop.md)
9. [08 — Evidence graph and two-pass structured response](08_Feature_08_evidence_graph_and_two_pass_structured_response.md)
10. [09 — Claim-level citation and freshness verifier](09_Feature_09_claim_level_citation_and_freshness_verifier.md)
11. [10 — Indirect prompt-injection defense](10_Feature_10_indirect_prompt_injection_defense.md)
12. [11 — Approval-gated Jira proposal](11_Feature_11_approval_gated_Jira_proposal.md)
13. [12 — Idempotent connector execution and recovery](12_Feature_12_idempotent_connector_execution_and_recovery.md)
14. [13 — Complete audit trace and run diff](13_Feature_13_complete_audit_trace_and_run_diff.md)
15. [14 — Replay scenario compiler](14_Feature_14_replay_scenario_compiler.md)
16. [15 — Readiness gate and CI release decision](15_Feature_15_readiness_gate_and_CI_release_decision.md)
17. [16 — Human review and practitioner scoring](16_Feature_16_human_review_and_practitioner_scoring.md)
18. [17 — One validated multilingual slice](17_Feature_17_one_validated_multilingual_slice.md)
19. [18 — Snapshot-first public mode and rate-limited live mode](18_Feature_18_snapshot_first_public_mode_and_rate_limited_live_mode.md)

## Embedded assets

Document 00 references three locally packaged PNG assets under `assets/00_ResolveFlow_Replay_Project_Overview_and_Feature_Catalog/media/`: the system architecture, Replay lifecycle, and public demo wireframe.
