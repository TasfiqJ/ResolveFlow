from __future__ import annotations

import json

from resolveflow.agent.contracts import (
    ChatRequest,
    ChatResponse,
    FinishReason,
    PassKind,
    ProviderUsage,
    ToolCallRequest,
)


class FixtureChatAdapter:
    """Deterministic two-pass provider fixture; it never performs network I/O."""

    provider_name = "recorded_fixture"

    def chat(self, request: ChatRequest) -> ChatResponse:
        if request.pass_kind is PassKind.STRUCTURE:
            return self._structure(request)
        has_tool_result = any(message.get("role") == "tool" for message in request.messages)
        if not has_tool_result:
            return ChatResponse(
                response_id="fixture-evidence-tool-round",
                model=request.model,
                finish_reason=FinishReason.TOOL_CALL,
                text="",
                tool_calls=(
                    ToolCallRequest(
                        tool_call_id="tool_rollout_001",
                        name="query_rollout_record",
                        arguments_json=json.dumps({"rollout_id": "rollout-payments-2026-07-15"}),
                    ),
                    ToolCallRequest(
                        tool_call_id="tool_incident_001",
                        name="query_prior_incident",
                        arguments_json=json.dumps({"error_code": "PYM-431"}),
                    ),
                ),
                usage=ProviderUsage(input_tokens=80, output_tokens=24),
            )
        return ChatResponse(
            response_id="fixture-evidence-findings",
            model=request.model,
            finish_reason=FinishReason.COMPLETE,
            text=json.dumps(self._findings(request), sort_keys=True),
            citation_ids=("cite_route", "cite_rollout", "cite_cluster"),
            usage=ProviderUsage(input_tokens=180, output_tokens=160),
        )

    @staticmethod
    def _findings(request: ChatRequest) -> dict[str, object]:
        by_artifact = {item.artifact_id: item for item in request.documents}
        claims: list[dict[str, object]] = []
        citations: list[dict[str, str]] = []
        runbook = by_artifact.get("artifact_runbook_payments")
        rollout = by_artifact.get("artifact_rollout_records")
        prior = by_artifact.get("artifact_prior_incident_1042")
        if runbook is not None:
            route_quote = "Route issuer-routing failures to Payments Platform."
            cluster_quote = (
                "Before rollback, identify the affected cluster and compare the error rate before "
                "and after the rollout."
            )
            citations.extend(
                [
                    {
                        "citation_id": "cite_route",
                        "document_id": runbook.document_id,
                        "exact_quote": route_quote,
                    },
                    {
                        "citation_id": "cite_cluster",
                        "document_id": runbook.document_id,
                        "exact_quote": cluster_quote,
                    },
                ]
            )
            claims.extend(
                [
                    {
                        "claim_id": "claim_route_payments",
                        "kind": "route",
                        "text": "Route issuer-routing failures to Payments Platform.",
                        "subject": "route",
                        "value": "Payments Platform",
                        "material": True,
                        "current_support_required": True,
                        "action_supporting": False,
                        "citation_ids": ["cite_route"],
                    },
                    {
                        "claim_id": "claim_verify_cluster",
                        "kind": "recommendation",
                        "text": (
                            "Identify the affected cluster and compare error rates before rollback."
                        ),
                        "subject": "rollback_precondition",
                        "value": "affected cluster",
                        "material": True,
                        "current_support_required": True,
                        "action_supporting": False,
                        "citation_ids": ["cite_cluster"],
                    },
                ]
            )
        if rollout is not None:
            rollout_quote = (
                "rollout-payments-2026-07-15,tenant_heliopay_synthetic,payments-api,"
                "ca-central,issuer-routing-v3,completed,2026-07-15T14:05:00Z,true"
            )
            citations.append(
                {
                    "citation_id": "cite_rollout",
                    "document_id": rollout.document_id,
                    "exact_quote": rollout_quote,
                }
            )
            claims.append(
                {
                    "claim_id": "claim_rollout_completed",
                    "kind": "fact",
                    "text": "The issuer-routing-v3 rollout completed.",
                    "subject": "rollout_change",
                    "value": "issuer-routing-v3",
                    "material": True,
                    "current_support_required": True,
                    "action_supporting": False,
                    "citation_ids": ["cite_rollout"],
                }
            )
        if prior is not None and runbook is not None:
            citations.append(
                {
                    "citation_id": "cite_action_route",
                    "document_id": prior.document_id,
                    "exact_quote": '"route":"Payments Platform"',
                }
            )
            claims.append(
                {
                    "claim_id": "claim_action_team",
                    "kind": "action",
                    "text": "Route the proposal to Payments Platform.",
                    "subject": "proposal_team",
                    "value": "Payments Platform",
                    "material": True,
                    "current_support_required": True,
                    "action_supporting": True,
                    "citation_ids": ["cite_action_route"],
                }
            )
        return {
            "schema_version": "1.0",
            "claims": claims,
            "citations": citations,
            "unknowns": [
                {
                    "unknown_id": "unknown_cluster_id",
                    "field": "cluster_id",
                    "text": "The affected cluster ID is not available.",
                    "reason_code": "context_not_found",
                }
            ],
            "requested_proposal": "create_jira_issue" if prior and runbook else "none",
        }

    @staticmethod
    def _structure(request: ChatRequest) -> ChatResponse:
        graph_message = next(
            message for message in request.messages if message.get("role") == "user"
        )
        graph = json.loads(str(graph_message["content"]))
        claims = graph["claims"]
        supported = {item["claim_id"]: item for item in claims if item["status"] == "supported"}
        route = next(
            (item["claim_id"] for item in supported.values() if item["kind"] == "route"),
            None,
        )
        facts = tuple(item["claim_id"] for item in supported.values() if item["kind"] == "fact")
        steps = tuple(
            item["claim_id"] for item in supported.values() if item["kind"] == "recommendation"
        )
        resolved = route is not None and not graph["conflicts"]
        body = {
            "schema_version": "1.0",
            "disposition": "resolved" if resolved else "needs_review",
            "route_claim_id": route if resolved else None,
            "summary_claim_ids": facts,
            "recommended_step_claim_ids": steps if resolved else (),
            "unknown_ids": [item["unknown_id"] for item in graph["unknowns"]],
            "conflict_ids": [item["conflict_id"] for item in graph["conflicts"]],
            "graph_hash": graph["graph_hash"],
            "needs_review": not resolved,
        }
        return ChatResponse(
            response_id="fixture-structure",
            model=request.model,
            finish_reason=FinishReason.COMPLETE,
            text=json.dumps(body, sort_keys=True),
            usage=ProviderUsage(input_tokens=120, output_tokens=64),
        )
