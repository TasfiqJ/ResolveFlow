# Replay truth review workflow

All catalog and scenario content in this directory is `DRAFT_PENDING_HUMAN_REVIEW` and
synthetic-agent-authored. Nothing here is human-authored or held-out locked.

A qualified reviewer should independently inspect each truth's T0 timeline, route, evidence
roles, answerability, unknowns, permitted action, and mutation behavior. Disagreements create a
new catalog version; they do not overwrite evaluated content. Only a signed review artifact may
change `human_review_status`, and a separate later task may create a held-out lock after the gate
and build commits are established. Until then, held-out candidates must not enter final release
claims or tuning.
