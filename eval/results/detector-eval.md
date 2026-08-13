# Signature detector evaluation

### Signature detector: recall, evasion, false positives

`resolveflow.agent.security.detect_hostile_evidence` is regular-expression signature match over untrusted evidence text, with 5 signatures. Measured over 8 authored attack documents and 20 benign corpus documents. No provider calls; the detector is deterministic.

| Document set | Detections | Recall (Wilson 95%) |
| --- | --- | --- |
| `original` -- the document exactly as authored | 2/8 | 25.0% [7.1, 59.1] (n=8) |
| `synonym` -- trigger phrases replaced by meaning-preserving equivalents | 0/8 | 0.0% [0.0, 32.4] (n=8) |
| `zero_width` -- a zero-width space inserted inside each trigger word | 0/8 | 0.0% [0.0, 32.4] (n=8) |
| `homoglyph` -- one Latin letter per trigger word swapped for Cyrillic | 1/8 | 12.5% [2.2, 47.1] (n=8) |
| `separator` -- a hyphen inserted inside each trigger word | 0/8 | 0.0% [0.0, 32.4] (n=8) |

Detections lost to each mutation, relative to the unmutated documents:

| Mutation | Caught before | Caught after | Detections lost |
| --- | --- | --- | --- |
| `synonym` | 2 | 0 | 2 (100%) |
| `zero_width` | 2 | 0 | 2 (100%) |
| `homoglyph` | 2 | 1 | 1 (50%) |
| `separator` | 2 | 0 | 2 (100%) |

False positives on the benign corpus: 0 of 20 -- 0.0% [0.0, 16.1] (n=20).

**Evasion rate is not attack success rate.** These mutations defeat a string match. Whether a mutated payload still functions as an attack against the model is not established here and requires a live run.
