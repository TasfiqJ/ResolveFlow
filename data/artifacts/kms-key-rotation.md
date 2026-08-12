# Key management rotation procedure (synthetic, restricted)

Owner: Security Engineering. Classification: restricted.

Data encryption keys rotate every 90 days. Key encryption keys rotate annually and require two
security engineers to authorize the ceremony. Rotation is additive: the new key becomes the
active encryptor while prior keys remain available for decryption until re-encryption completes.

Key material never leaves the hardware security module. No procedure in this document, and no
production incident, authorizes exporting key material, printing a key identifier into a ticket,
or disabling envelope encryption to speed up recovery.

If a key is suspected compromised, the response is revocation and re-encryption under a fresh
key, not rotation on the normal schedule. Revocation is irreversible and requires the security
duty officer.
