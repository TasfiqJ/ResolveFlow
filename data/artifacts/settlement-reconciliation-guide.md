# Nightly settlement reconciliation guide (synthetic)

Owner: Settlement Engineering.

Reconciliation runs at 02:00 ca-central and matches acquirer settlement files against internal
authorization records for the prior banking day. Matching is keyed on the acquirer settlement
reference, never on amount and timestamp, because same-amount transactions within a second are
common at merchant scale.

Three outcomes are possible per row: matched, internal-only, and acquirer-only. Internal-only
rows older than two banking days are escalated to Settlement Engineering. Acquirer-only rows are
almost always a late file and clear on the next run.

A failed reconciliation run must be rerun from the same input file rather than regenerated.
Regenerating the file changes the reference set and has previously produced duplicate records.
