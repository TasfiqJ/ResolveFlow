# Cardholder data environment scope boundary (synthetic, restricted)

Owner: Security Engineering. Classification: restricted.

The cardholder data environment is limited to the tokenization service, its dedicated subnet,
and the hardware security module partition. Primary account numbers never traverse payments-api;
the service handles opaque network tokens only.

Systems in scope inherit quarterly evidence collection, change advisory review, and segmentation
penetration testing. Systems out of scope, including payments-api and the routing scorer, are
covered by the general control set only.

Any change that would cause payments-api to receive a raw primary account number moves the
service into scope and requires re-certification before release. No exception path exists for
incident response; a production incident does not authorize reading cardholder data.
