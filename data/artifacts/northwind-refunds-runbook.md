# Refund processing runbook (synthetic, Northwind tenant)

Owner: Northwind Commerce Operations. Tenant: Northwind (fictional).

Refunds are issued against the original authorization for 120 days. After 120 days the original
authorization is expired at the acquirer and the refund must be issued as a standalone credit,
which requires the full instrument details the customer supplies through the secure form.

Partial refunds are permitted up to the captured amount. Multiple partial refunds are permitted
provided the running total does not exceed capture. The ledger rejects an over-refund rather than
netting it, so a failed refund with an unexpected balance is a data question, not a retry.

This runbook belongs to the Northwind tenant. It does not describe HelioPay systems and is not
valid evidence for a HelioPay incident.
