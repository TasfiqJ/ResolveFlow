from __future__ import annotations

import hashlib
import json
from pathlib import Path

from resolveflow.domain.hashing import checksum
from resolveflow.domain.models import RunSnapshot
from resolveflow.evaluation.integrity import EvaluationIntegrityAudit
from resolveflow.evaluation.io import verify_bundle_file


def main() -> None:
    hero_path = Path("data/published/hero-foundation.json")
    hero = RunSnapshot.model_validate(json.loads(hero_path.read_text(encoding="utf-8")))
    if checksum(hero.model_dump(mode="python", exclude={"content_hash"})) != hero.content_hash:
        raise SystemExit("hero snapshot content hash mismatch")
    web_hero = Path("apps/web/public/snapshots/hero-foundation.json")
    if web_hero.read_bytes() != hero_path.read_bytes():
        raise SystemExit("web hero snapshot differs from canonical published snapshot")
    live_path = Path("data/published/hero-cohere-live.json")
    if live_path.exists():
        live = RunSnapshot.model_validate(json.loads(live_path.read_text(encoding="utf-8")))
        if checksum(live.model_dump(mode="python", exclude={"content_hash"})) != live.content_hash:
            raise SystemExit("live hero snapshot content hash mismatch")
        if live.provenance != "live_provider" or live.response.provider != "cohere":
            raise SystemExit("live hero snapshot does not have live-provider provenance")
        if not live.provider_traces or not any(
            trace.get("usage", {}).get("input_tokens", 0) > 0 for trace in live.provider_traces
        ):
            raise SystemExit("live hero snapshot has no provider usage evidence")
        if (
            live.retrieval.embedding_model == "fixture-embed-v1"
            or live.retrieval.rerank_model == "fixture-rerank-v1"
        ):
            raise SystemExit("live hero snapshot used a fixture retrieval adapter")
        candidates = {item.chunk_id: item for item in live.retrieval.candidates}
        claims = {item.get("claim_id") for item in live.evidence_graph.get("claims", [])}
        if not live.response.citations:
            raise SystemExit("live hero snapshot has no verifier-accepted citation")
        for citation in live.response.citations:
            candidate = candidates.get(citation.source_id)
            if candidate is None or citation.claim_id not in claims:
                raise SystemExit("live citation does not close over a retrieved source and claim")
            if citation.excerpt not in candidate.content:
                raise SystemExit("live citation excerpt is not exact source text")
            required = {
                "citation_exists",
                "citation_authorized",
                "citation_version_valid",
                "citation_fresh",
                "citation_in_context",
                "citation_span_exact",
                "citation_supports_claim",
            }
            if not required.issubset(citation.verifier_codes):
                raise SystemExit("live citation did not pass every deterministic check")
        previous_hash: str | None = None
        for event in live.trace:
            if event.previous_event_hash != previous_hash:
                raise SystemExit("live hero audit chain link mismatch")
            if (
                checksum(event.model_dump(mode="python", exclude={"event_id", "event_hash"}))
                != event.event_hash
            ):
                raise SystemExit("live hero audit event hash mismatch")
            previous_hash = event.event_hash
        web_live = Path("apps/web/public/snapshots/hero-cohere-live.json")
        if web_live.read_bytes() != live_path.read_bytes():
            raise SystemExit("web live hero snapshot differs from canonical published snapshot")
    result_path = Path("data/published/replay-development-result.json")
    verify_bundle_file(result_path)
    web_result = Path("apps/web/public/snapshots/replay-development-result.json")
    if web_result.read_bytes() != result_path.read_bytes():
        raise SystemExit("web result snapshot differs from canonical published result")
    audit_path = Path("data/published/evaluation-integrity-audit.json")
    audit = EvaluationIntegrityAudit.model_validate(
        json.loads(audit_path.read_text(encoding="utf-8"))
    )
    if checksum(audit.model_dump(mode="python", exclude={"checksum"})) != audit.checksum:
        raise SystemExit("evaluation integrity audit canonical checksum mismatch")
    expected_file_hash = audit_path.with_suffix(".json.sha256").read_text().split()[0]
    if hashlib.sha256(audit_path.read_bytes()).hexdigest() != expected_file_hash:
        raise SystemExit("evaluation integrity audit file checksum mismatch")
    web_audit = Path("apps/web/public/snapshots/evaluation-integrity-audit.json")
    if web_audit.read_bytes() != audit_path.read_bytes():
        raise SystemExit("web evaluation integrity audit differs from canonical artifact")
    print(
        "Public snapshot integrity passed: recorded hero, optional live hero, Replay result, "
        "and evaluation integrity checksums verified"
    )


if __name__ == "__main__":
    main()
