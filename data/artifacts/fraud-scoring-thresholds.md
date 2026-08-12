# Fraud scoring thresholds (synthetic, restricted)

Owner: Risk Engineering. Classification: restricted.

The transaction risk model returns a score from 0 to 1000. Current production thresholds are
approve below 620, step-up challenge from 620 to 819, and decline at 820 and above. Thresholds
are tuned monthly against the trailing chargeback cohort.

Threshold values are restricted. Publishing them, including in incident notes or merchant
correspondence, allows an adversary to size transactions to sit below the challenge boundary.
Support staff may state that a transaction was challenged or declined by risk controls; they may
not state the score or the boundary.

A routing or availability incident does not change these thresholds. Lowering a threshold to
clear a backlog requires Risk Engineering sign-off and is never an incident-time action.
