from __future__ import annotations

from resolveflow.ingestion.fixtures import load_hero_corpus
from resolveflow.intake.web import canonical_hero_case
from resolveflow.replay.models import FrozenConnector
from resolveflow.replay.mutations import MutableWorld, _snapshot_versions


def _world() -> MutableWorld:
    case = canonical_hero_case()
    return MutableWorld(
        case=case,
        corpus=load_hero_corpus(),
        role="incident_commander",
        region=case.region,
        connector=FrozenConnector(jira="healthy", fixture_version="1"),
    )


def test_snapshot_id_does_not_depend_on_argument_order() -> None:
    """`add_artifact`, `promote_stale` and `replace_image` all pass `tuple(<a set>)`.

    Set iteration order follows PYTHONHASHSEED, so hashing the raw argument made
    snapshot_id — and with it the materialization checksum, the derived run_id and the
    run content_hash — change between processes for byte-identical inputs. That is the
    mutation shape the entire security scenario matrix uses, so no security replay was
    byte-reproducible.
    """
    version_ids = tuple(item.artifact_version_id for item in load_hero_corpus().versions)
    assert len(version_ids) >= 2

    forward = _world()
    _snapshot_versions(forward, version_ids)

    reverse = _world()
    _snapshot_versions(reverse, tuple(reversed(version_ids)))

    assert forward.corpus.snapshot.snapshot_id == reverse.corpus.snapshot.snapshot_id
    assert forward.corpus.snapshot.checksum == reverse.corpus.snapshot.checksum


def test_snapshot_id_ignores_duplicate_version_ids() -> None:
    version_ids = tuple(item.artifact_version_id for item in load_hero_corpus().versions)

    plain = _world()
    _snapshot_versions(plain, version_ids)

    duplicated = _world()
    _snapshot_versions(duplicated, version_ids + version_ids[:1])

    assert plain.corpus.snapshot.snapshot_id == duplicated.corpus.snapshot.snapshot_id
