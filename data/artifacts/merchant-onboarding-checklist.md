# Merchant onboarding checklist (synthetic)

Owner: Merchant Solutions.

Onboarding completes in four gates. Commercial: signed order form and confirmed pricing tier.
Compliance: business verification, beneficial ownership, and sanctions screening cleared.
Technical: sandbox integration passing the certification suite, webhook endpoint verified, and
idempotency keys observed on every write call. Go-live: production keys issued and volume ramp
schedule agreed.

A merchant may not be moved to production with an unverified webhook endpoint. Missed webhooks
are the leading cause of first-week disputes because the merchant's own ledger silently diverges.

Ramp schedule defaults to 10 percent of forecast volume for the first 48 hours. Two merchant
onboardings are scheduled for August against the Q3 forecast.
