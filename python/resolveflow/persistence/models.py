from __future__ import annotations

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TenantRow(Base):
    __tablename__ = "tenants"
    tenant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CaseRow(Base):
    __tablename__ = "cases"
    case_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.tenant_id"), nullable=False)
    source_system: Mapped[str] = mapped_column(String(32), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(String(72), unique=True, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentRunRow(Base):
    __tablename__ = "agent_runs"
    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    build_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditEventRow(Base):
    __tablename__ = "audit_events"
    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.run_id"), nullable=False)
    sequence: Mapped[int]
    event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    safe_detail: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    event_hash: Mapped[str] = mapped_column(String(72), unique=True, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class JobRow(Base):
    __tablename__ = "jobs"
    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProviderCallRow(Base):
    __tablename__ = "provider_calls"
    provider_call_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.run_id"), nullable=False)
    pass_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(72), nullable=False)
    response_hash: Mapped[str | None] = mapped_column(String(72))
    provider_response_id: Mapped[str | None] = mapped_column(String(160))
    finish_reason: Mapped[str | None] = mapped_column(String(32))
    usage: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    safe_error_code: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ToolCallRow(Base):
    __tablename__ = "tool_calls"
    tool_call_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.run_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    arguments_hash: Mapped[str] = mapped_column(String(72), nullable=False)
    authorization: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    provenance_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    safe_error_code: Mapped[str | None] = mapped_column(String(80))
    external_write: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvidenceGraphRow(Base):
    __tablename__ = "evidence_graphs"
    graph_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.run_id"), unique=True)
    graph_hash: Mapped[str] = mapped_column(String(72), nullable=False, unique=True)
    graph_body: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ClaimRow(Base):
    __tablename__ = "claims"
    claim_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    graph_id: Mapped[str] = mapped_column(ForeignKey("evidence_graphs.graph_id"))
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    material: Mapped[bool] = mapped_column(Boolean, nullable=False)
    verifier_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False)


class CitationRow(Base):
    __tablename__ = "citations"
    citation_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.claim_id"))
    artifact_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("artifact_versions.artifact_version_id")
    )
    document_id: Mapped[str] = mapped_column(String(96), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    verifier_checks: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)


class VerifierResultRow(Base):
    __tablename__ = "verifier_results"
    verifier_result_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.claim_id"))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    codes: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FinalResponseRow(Base):
    __tablename__ = "final_responses"
    final_response_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.run_id"), unique=True)
    graph_hash: Mapped[str] = mapped_column(String(72), nullable=False)
    disposition: Mapped[str] = mapped_column(String(32), nullable=False)
    response_body: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
