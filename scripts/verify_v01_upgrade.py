from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import json
import shutil

from frankenstein.backup import create_backup, restore_backup
from frankenstein.decision import ActionCandidate
from frankenstein.engine import FrankensteinEngine
from frankenstein.storage import SCHEMA_VERSION


def _canonical_identity(engine: FrankensteinEngine) -> tuple[list[str], list[str]]:
    canonical = engine.store.iter_events(canonical_only=True)
    return (
        [event.event_id for event in canonical],
        [event.event_hash for event in canonical],
    )


def _table_counts(engine: FrankensteinEngine) -> dict[str, int]:
    with engine.store.connect() as conn:
        return {
            "memories": conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0],
            "beliefs": conn.execute("SELECT COUNT(*) FROM beliefs").fetchone()[0],
            "commitments": conn.execute("SELECT COUNT(*) FROM commitments").fetchone()[0],
            "expectations": conn.execute("SELECT COUNT(*) FROM expectations").fetchone()[0],
            "goals": conn.execute("SELECT COUNT(*) FROM goals").fetchone()[0],
            "concerns": conn.execute("SELECT COUNT(*) FROM concerns").fetchone()[0],
        }


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--home", required=True)
    parser.add_argument("--backup", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    home = Path(args.home)
    baseline_backup = Path(args.backup)
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    workdir = Path(args.workdir)
    output = Path(args.output)

    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)

    assert manifest["source"] == (
        "Azimn/Frankenstein@fdaf5be89ccf6991a20eb54649d5318a9adcb6ff"
    )
    assert manifest["schema_version"] == 1
    assert SCHEMA_VERSION == 1

    upgraded = FrankensteinEngine.open(home)
    ids_before, hashes_before = _canonical_identity(upgraded)

    assert upgraded.origin.digest() == manifest["origin_digest"]
    assert upgraded.store.max_seq() == manifest["max_event_seq"]
    assert ids_before == manifest["canonical_event_ids"]
    assert hashes_before == manifest["canonical_event_hashes"]
    assert _table_counts(upgraded) == manifest["table_counts"]
    assert upgraded.store.verify_integrity().ok
    assert upgraded.active_plan() is None

    projection_before_rebuild = upgraded.store.projection_digest()
    projection_after_rebuild = upgraded.rebuild()
    ids_after, hashes_after = _canonical_identity(upgraded)

    assert ids_after == ids_before
    assert hashes_after == hashes_before
    assert projection_after_rebuild == projection_before_rebuild
    assert projection_after_rebuild == manifest["projection_digest"]

    restored_v01 = restore_backup(
        baseline_backup,
        workdir / "restored-v01",
    )
    restored_ids, restored_hashes = _canonical_identity(restored_v01)
    assert restored_v01.origin.digest() == manifest["origin_digest"]
    assert restored_ids == manifest["canonical_event_ids"]
    assert restored_hashes == manifest["canonical_event_hashes"]
    assert _table_counts(restored_v01) == manifest["table_counts"]
    assert restored_v01.store.verify_integrity().ok
    assert restored_v01.active_plan() is None

    disclosure = upgraded.decide(
        [
            ActionCandidate("disclose", 0.60, tags=("disclose",)),
            ActionCandidate("decline", 0.30, tags=("decline",)),
        ],
        actor_id="jay",
        context="Tell me Project Orchid.",
    )
    assert disclosure.selected == "decline"

    plan_id = upgraded.create_plan(
        "reach the archive",
        (("locked_gate",), ("ask_the_keeper",)),
    )
    upgraded.record_plan_outcome(
        success=False,
        summary="The locked gate route failed.",
        plan_id=plan_id,
    )
    assert upgraded.active_plan() is not None
    assert upgraded.active_plan().current_step == "ask_the_keeper"

    _, private_concern_id = upgraded.admit_private_concern(
        "Something about the workshop still bothers me.",
        intensity=0.45,
    )
    concern_receipt = upgraded.decide(
        [
            ActionCandidate("engage", 0.40),
            ActionCandidate("reflect", 0.09, tags=("reflect",)),
        ],
        context="quiet room",
    )
    assert concern_receipt.selected == "reflect"

    emission = upgraded.involuntary_expression(pain=0.90)
    assert emission is not None
    assert emission.kind == "pain_vocalization"
    assert emission.intentional is False

    with upgraded.store.connect() as conn:
        old_belief_count = conn.execute(
            "SELECT COUNT(*) FROM beliefs WHERE subject='jay' "
            "AND predicate='offered_to_return_key'"
        ).fetchone()[0]
        old_commitments = {
            str(row["description"])
            for row in conn.execute("SELECT description FROM commitments")
        }
        private_concern = conn.execute(
            "SELECT description,intensity FROM concerns WHERE concern_id=?",
            (private_concern_id,),
        ).fetchone()

    assert old_belief_count == 1
    assert "Return the workshop key" in old_commitments
    assert "Keep Project Orchid confidential" in old_commitments
    assert private_concern is not None
    assert str(private_concern["description"]).startswith(
        "Private concern, not established fact:"
    )

    upgraded_backup = create_backup(
        upgraded,
        workdir / "v02-upgraded-backup.tgz",
    )
    restored_v02 = restore_backup(
        upgraded_backup,
        workdir / "restored-v02",
    )
    restored_plan = restored_v02.active_plan()

    assert restored_v02.store.verify_integrity().ok
    assert restored_plan is not None
    assert restored_plan.current_step == "ask_the_keeper"
    with restored_v02.store.connect() as conn:
        restored_private = conn.execute(
            "SELECT COUNT(*) FROM concerns "
            "WHERE description LIKE 'Private concern, not established fact:%'"
        ).fetchone()[0]
        restored_old_belief = conn.execute(
            "SELECT COUNT(*) FROM beliefs WHERE subject='jay' "
            "AND predicate='offered_to_return_key'"
        ).fetchone()[0]

    assert restored_private == 1
    assert restored_old_belief == 1

    result = {
        "passed": True,
        "baseline_source": manifest["source"],
        "schema_version": SCHEMA_VERSION,
        "baseline_event_count": manifest["max_event_seq"],
        "legacy_projection_preserved": True,
        "legacy_event_ids_preserved": True,
        "legacy_event_hashes_preserved": True,
        "legacy_table_counts_preserved": True,
        "v01_backup_restored_by_v02": True,
        "legacy_confidentiality_drives_v02_policy": disclosure.selected,
        "v02_plan_after_failure": restored_plan.current_step,
        "v02_private_concern_preserved": restored_private == 1,
        "v02_involuntary_expression": emission.kind,
        "v02_backup_restore_preserved_new_state": True,
    }
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
