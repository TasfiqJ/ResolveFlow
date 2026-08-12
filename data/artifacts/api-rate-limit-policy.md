# Public API rate limit policy (synthetic)

Owner: Developer Platform. Classification: public.

Sandbox keys are limited to 10 requests per second per key with a burst allowance of 30.
Production keys are limited to 200 requests per second per merchant account with a burst of 500.
Limits are enforced per merchant account, not per key, so rotating keys does not raise a ceiling.

Requests over the limit return HTTP 429 with a Retry-After header in whole seconds. Clients are
expected to honor Retry-After and apply exponential backoff with jitter. Retrying a 429 without
backoff is the single most common cause of a merchant remaining throttled.

Rate limiting is independent of authorization outcomes. A throttled request was never routed to
an acquirer and must not be treated as a decline.
