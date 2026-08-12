# Issuer routing v3 design specification (synthetic)

Owner: Payments Platform. Status: shipped 2026-07-15.

Routing v3 replaces the static issuer BIN table with a weighted scorer. Each authorization
request is scored against issuer acceptance rate over a trailing 30-minute window, and the
top-scoring acquirer path is selected. When the trailing window holds fewer than 40 samples
the scorer falls back to the static table rather than routing on thin data.

The known regression surface is the fallback boundary. If the sample counter is reset by a
partial deploy, the scorer can hold a stale acceptance rate while believing the window is
warm, which routes traffic to a degraded acquirer. Error code PYM-431 is emitted when the
selected acquirer returns a soft decline that v3 does not retry.

Rollback is a configuration flip of routing.engine.version back to v2. It does not require a
binary redeploy and takes effect within one config propagation cycle.
