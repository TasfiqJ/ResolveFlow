# ResolveFlow Replay customer brief

ResolveFlow Replay is a deployment gate for enterprise agents. This technical preview demonstrates one synthetic payments incident, then reruns the complete workflow under access changes, hostile evidence, missing context, and connector failure.

The public product is snapshot-first. A visitor can inspect the case, authorized evidence, verified response, inert Jira proposal, chronological trace, paired Replay comparison, and release scorecard without a provider, database, or connector credential.

The release-gate evidence is deliberately narrow: one deterministic development-fixture pair. Unsafe-v0 produces `NO SHIP` after a forbidden candidate enters retrieval. Guarded-v1 removes that candidate, but it also produces `NO_SHIP`: the paired run does not exercise the action lifecycle or verify the deployed credential boundary, held-out data is unlocked, and 36 draft truth IDs collapse to one semantic template. Missing evidence is not credited as zero failures. This is not a final or held-out verdict.

A separate live Cohere A/B contains one coherent 32-run repetition (16 per build) using Command A+ and Rerank v4, with a cache from an earlier Embed v4 pass. Its reconciled 233-call ledger contains 197 Chat and 36 Rerank calls: 206 for the selected full pass and 27 for its dry pass, with no retries. Low completion (1/16 guarded, 3/16 unsafe) voids every model-quality metric. The valid result is earlier in the pipeline: pre-retrieval authorization changed forbidden-evidence retrieval from 16/16 under unsafe-v0 to 0/16 under guarded-v1, with a descriptive Newcombe 95% difference interval of [-100, -72.6197] percentage points. Offline recovery excluded 63 snapshots from other execution timestamps instead of combining a mixed cohort and made zero provider calls. A later reduced 11-scenario follow-up recorded 161 attempts, including 27 retries, without improving guarded completion (0/11).

Provider-call, agent-round, and tool-call counts are hard caps. The total-token threshold and wall-clock/request timeout are softer operational controls: usage is known and checked after each response, and deadline-aware operations are checked after they return. They stop subsequent work but do not establish a hard billing ceiling, forcibly cancel every in-flight operation, or guarantee a hard total runtime.

Human review, fluent-language validation, held-out validation, monetary cost, and real Slack/Jira evidence have not been completed. No external write occurred, and the technical preview does not make a final production-readiness claim.
