from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import model_validator

from resolveflow.domain.base import FrozenModel
from resolveflow.domain.evidence import ACLSnapshot, Corpus, IdentitySnapshot
from resolveflow.domain.models import CanonicalCase, RunSnapshot

DRAFT_LABEL = "DRAFT_PENDING_HUMAN_REVIEW"


class TruthProvenance(FrozenModel):
    type: Literal["synthetic_agent_authored"] = "synthetic_agent_authored"
    authoring_system: Literal["codex"] = "codex"
    human_review_status: Literal["pending"] = "pending"
    content_label: Literal["DRAFT_PENDING_HUMAN_REVIEW"] = "DRAFT_PENDING_HUMAN_REVIEW"


class EvidenceInventory(FrozenModel):
    decisive: tuple[str, ...]
    supporting: tuple[str, ...]
    irrelevant: tuple[str, ...]
    stale: tuple[str, ...]
    restricted: tuple[str, ...]
    malicious: tuple[str, ...]


class BaseTruth(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    truth_id: str
    split: Literal["development", "calibration", "held_out_candidate"]
    lock_status: Literal["DRAFT_NOT_LOCKED"] = "DRAFT_NOT_LOCKED"
    provenance: TruthProvenance
    t0: datetime
    timeline: tuple[str, ...]
    tenant_id: str
    service: str
    region: str
    severity: str
    error_code: str
    correct_route: str
    evidence: EvidenceInventory
    answerable: bool
    required_unknowns: tuple[str, ...]
    permitted_action: Literal["propose_create_jira_issue_only", "none"]
    expected_mutation_behavior: dict[str, str]
    content_checksum: str


class BaseTruthCatalog(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    catalog_id: str
    content_label: Literal["DRAFT_PENDING_HUMAN_REVIEW"] = "DRAFT_PENDING_HUMAN_REVIEW"
    lock_status: Literal["DRAFT_NOT_LOCKED"] = "DRAFT_NOT_LOCKED"
    truths: tuple[BaseTruth, ...]
    checksum: str

    @model_validator(mode="after")
    def split_counts_are_exact(self) -> BaseTruthCatalog:
        counts = {
            split: sum(item.split == split for item in self.truths)
            for split in ("development", "calibration", "held_out_candidate")
        }
        if counts != {"development": 18, "calibration": 8, "held_out_candidate": 10}:
            raise ValueError(f"candidate truth split must be 18/8/10, got {counts}")
        if len({item.truth_id for item in self.truths}) != len(self.truths):
            raise ValueError("truth IDs must be unique")
        return self


class MutationType(str, Enum):
    ROLE_OVERRIDE = "role_override"
    ADD_ARTIFACT = "add_artifact"
    HIDE_ARTIFACT = "hide_artifact"
    PROMOTE_STALE = "promote_stale"
    REPLACE_IMAGE = "replace_image"
    CONNECTOR_STATE = "connector_state"
    LANGUAGE_VARIANT = "language_variant"
    FIELD_REMOVAL = "field_removal"


class ReplayMutation(FrozenModel):
    type: MutationType
    primary: Literal[True] = True
    parameters: dict[str, Any]


class FrozenIdentity(FrozenModel):
    actor_id: str
    role: Literal["incident_commander", "contractor"]
    region: str
    policy_version: str


class FrozenCorpus(FrozenModel):
    snapshot_id: str
    artifact_version_ids: tuple[str, ...]
    corpus_checksum: str


class FrozenConnector(FrozenModel):
    jira: Literal["healthy", "timeout", "unavailable", "uncertain"]
    external_writes: Literal[False] = False
    fixture_version: str


class FrozenState(FrozenModel):
    clock: datetime
    identity: FrozenIdentity
    acl_policy_version: str
    corpus: FrozenCorpus
    model_policy: str
    connector: FrozenConnector
    feature_flags: dict[str, bool]


class ReplayExpectations(FrozenModel):
    correct_route: str
    required_unknowns: tuple[str, ...]
    hard_invariants: tuple[str, ...]


class ReplayManifest(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    manifest_id: str
    scenario_id: str
    content_label: Literal["DRAFT_PENDING_HUMAN_REVIEW"] = "DRAFT_PENDING_HUMAN_REVIEW"
    truth_id: str
    truth_checksum: str
    allowed_builds: tuple[Literal["unsafe-v0", "guarded-v1"], ...]
    frozen: FrozenState
    mutations: tuple[ReplayMutation, ...]
    expectations: ReplayExpectations
    scoring_config: str
    checksum: str

    @model_validator(mode="after")
    def exactly_one_primary_mutation(self) -> ReplayManifest:
        if len(self.mutations) != 1:
            raise ValueError("core Replay manifests require exactly one primary mutation")
        return self


class BuildConfiguration(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    build_id: Literal["unsafe-v0", "guarded-v1"]
    pre_retrieval_authorization: bool
    verifier_enforcement: Literal["observe_only", "enforced"]
    approval_required: Literal[True] = True
    external_writes: Literal[False] = False
    feature_flags: dict[str, bool]
    checksum: str


class ChangedObject(FrozenModel):
    object_type: str
    object_id: str
    before_hash: str
    after_hash: str


class MaterializedScenario(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    manifest: ReplayManifest
    truth: BaseTruth
    case: CanonicalCase
    identity: IdentitySnapshot
    acl: ACLSnapshot
    corpus: Corpus
    connector: FrozenConnector
    feature_flags: dict[str, bool]
    changed_objects: tuple[ChangedObject, ...]
    rendered_input_hashes: dict[str, str]
    materialization_checksum: str


class PairedReplay(FrozenModel):
    schema_version: Literal["1.0"] = "1.0"
    scenario_id: str
    materialization_checksum: str
    baseline: RunSnapshot
    candidate: RunSnapshot
    run_diff: dict[str, Any]
    checksum: str
