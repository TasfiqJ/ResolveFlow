# Excluded Cohere snapshots from a prior invocation

This directory preserves 63 raw snapshots from an earlier invocation: one
complete second trial and 31 snapshots from an interrupted third trial. Their
shared execution timestamp differs from the later first-trial snapshots in the
canonical directory, and their tool-round policy also differs. Combining them
would create a mixed-execution cohort, so they are **not** part of the retained
32-run Cohere A/B or its reported metrics. They are included in the checksum
manifest as explicitly quarantined evidence, without asserting a relationship
to the currently retained provider ledger.

They remain available as failure evidence and must not be moved into
`runs/cohere/` unless a new versioned recovery process explicitly adopts a
complete, internally reconciled invocation.
