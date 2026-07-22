# Stage 03 — governed agent and safety

Read:

- `docs/spec/00_ResolveFlow_Replay_Project_Overview_and_Feature_Catalog.md`
- `docs/spec/06_Feature_06_Rerank_v4_Fast_Pro_decision_policy.md`
- `docs/spec/07_Feature_07_bounded_Command_A_agent_loop.md`
- `docs/spec/08_Feature_08_evidence_graph_and_two_pass_structured_response.md`
- `docs/spec/09_Feature_09_claim_level_citation_and_freshness_verifier.md`
- `docs/spec/10_Feature_10_indirect_prompt_injection_defense.md`

Implement:

- bounded agent orchestration;
- typed allowlisted tools and fixed round/time/token/provider-call budgets;
- Cohere Chat adapter plus deterministic fixture adapter;
- evidence graph, claims, citations, conflicts, unknowns, and graph hashing;
- authorization/version/freshness/context/support verification;
- strict two-pass response contract;
- deterministic renderer and minimal verified fallback;
- prompt-injection fixture library and untrusted-evidence boundary;
- observable forbidden-effect scoring;
- policy linter;
- malformed-tool, timeout, hostile-evidence, and forbidden-authority tests;
- provider/tool traces without hidden reasoning.

The model must never perform an external write. The default suite must not require live Cohere. Expand `scripts/verify.sh`, run it, and leave the working tree ready for the outer loop.
