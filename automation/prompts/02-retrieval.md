# Stage 02 — evidence and retrieval

Read:

- `docs/spec/00_ResolveFlow_Replay_Project_Overview_and_Feature_Catalog.md`
- `docs/spec/03_Feature_03_corpus_ingestion_versioning_and_effective_time.md`
- `docs/spec/04_Feature_04_pre_retrieval_authorization_and_role_switch.md`
- `docs/spec/05_Feature_05_hybrid_retrieval_with_Embed_v4.md`
- `docs/spec/06_Feature_06_Rerank_v4_Fast_Pro_decision_policy.md`

Implement:

- synthetic corpus fixtures;
- artifact/version/chunk/ACL/embedding/corpus-snapshot schemas;
- stable IDs, checksums, parser/chunker provenance, and effective-time filtering;
- idempotent ingestion and data-quality validation;
- immutable identity and ACL snapshots;
- authorization before lexical and vector search;
- PostgreSQL full-text and pgvector retrieval;
- hybrid fusion, deduplication, and per-artifact diversity caps;
- Cohere Embed and Fast/Pro Rerank adapters behind interfaces;
- deterministic fixture adapters used by the default test path;
- candidate-level ranks, component scores, provenance, and trace;
- role-switch behavior and cache isolation;
- retrieval metrics and negative security tests.

Do not tune on held-out data or fabricate provider/retrieval results. Expand `scripts/verify.sh`, run it, and leave the working tree ready for the outer loop.
