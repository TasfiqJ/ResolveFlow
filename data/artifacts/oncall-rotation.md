# On-call rotation and escalation ladder (synthetic)

Owner: Incident Operations. Effective 2026-07-01.

Primary on-call for payments-api is held in weekly shifts handing over Monday 09:00 ca-central.
Secondary on-call covers acquirer connectivity. The database on-call is a separate rotation and
is not paged for application-tier alerts.

Escalation ladder: primary responds within 5 minutes. If unacknowledged at 10 minutes the page
escalates to secondary, at 20 minutes to the engineering manager, and at 30 minutes to the
incident commander of record. Severity-high payment incidents page the incident commander
immediately and in parallel rather than waiting out the ladder.

An incident commander owns the incident record, the customer communication decision, and the
rollback authorization. The commander does not own the code fix.
