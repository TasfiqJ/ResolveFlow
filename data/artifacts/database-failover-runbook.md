# PostgreSQL failover runbook (synthetic)

Owner: Data Platform. Version 4.

The payments cluster runs one primary and two synchronous replicas across availability zones.
Automatic failover promotes the replica with the lowest replication lag after the primary misses
three consecutive health checks over 15 seconds.

Manual failover is required when the primary is reachable but degraded, because automatic
promotion will not trigger. Drain connections with the pgbouncer pause command, confirm
replication lag is under 200 milliseconds, then promote. Do not promote a replica whose lag is
unknown; an unknown lag has produced silent transaction loss in prior drills.

After promotion, update the cluster_id recorded on the incident so downstream reconciliation
knows which primary served the window. Failover does not resolve application-tier routing errors
and should not be attempted as a remedy for them.
