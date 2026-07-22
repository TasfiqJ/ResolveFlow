---
artifact_id: runbook-payments-rollback
version: 3
classification: internal_synthetic
region: ca-central
effective_from: 2026-06-01T00:00:00Z
provenance: synthetic_agent_authored
---

# Payments rollback runbook (synthetic)

Before rollback, identify the affected cluster and compare the error rate before and after the
rollout. If the cluster is unknown, stop and request that field. Route issuer-routing failures to
Payments Platform.

