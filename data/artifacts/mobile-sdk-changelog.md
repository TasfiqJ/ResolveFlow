# Mobile SDK changelog (synthetic)

Owner: Client Platform.

Version 8.4.0, 2026-07-09. Adds network token refresh on foreground. Fixes a retry loop where a
429 from the rate limiter was treated as a transient network failure and retried immediately.

Version 8.3.2, 2026-06-21. Fixes a crash when the device clock is more than 24 hours behind,
which invalidated request signing. Adds a clock-skew warning to the SDK log.

Version 8.3.0, 2026-05-30. Introduces the deferred capture API. Deprecates the legacy charge
endpoint, which remains available through 2027-01-01.

The SDK does not implement issuer routing and is unaffected by routing engine version changes.
Client-side symptoms of a routing regression appear as elevated soft declines, not as SDK errors.
