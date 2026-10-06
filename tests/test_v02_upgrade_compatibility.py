from pathlib import Path
import json
import tarfile
import tempfile

from frankenstein.backup import create_backup, restore_backup
from frankenstein.cartridge import CharacterOrigin
from frankenstein.decision import ActionCandidate
from frankenstein.engine import FrankensteinEngine
from frankenstein.private_cognition import active_private_concerns


def origin():
    return CharacterOrigin(
        entity_id="upgrade-subject",
        display_name="Ada",
        action_priors={"engage": 0.03},
    )


def make_v01_shaped_home(path: Path) -> FrankensteinEngine:
    """Create state using only APIs and event kinds available in Frankenstein v0.1."""

    subject = FrankensteinEngine(path, origin())
    subject.update_relationship(
        "jay",
        {"trust": 0.25, "familiarity": 0.20},
    )
    subject.form_memory(
        "Jay left the workshop key in the north cabinet.",
        actor_id="jay",
        tags=("workshop", "key", "north", "cabinet"),
        salience=0.60,
    )
    subject.create_commitment(
        "Return the workshop key",
        actor_id="jay",
    )
    expectation_id = subject.create_expectation(
        "Jay returns tomorrow",
        actor_id="jay",
        confidence=0.70,
    )
    subject.update_expectation(
        expectation_id,
        "confirmed",
    )
    subject.set_concern(
        "The relay still needs inspection",
        intensity=0.35,
    )
    return subject


def test_v01_shaped_home_opens_without_migration(tmp_path):
    subject = make_v01_shaped_home(tmp_path / "home")
    before = subject.store.semantic_projection_digest()
    assert subject.active_plan() is None

    reopened = FrankensteinEngine.open(subject.home)

    assert reopened.store.get_meta("schema_version") == "1"
    assert reopened.store.verify_integrity().ok
    assert reopened.store.semantic_projection_digest() == before
    assert reopened.active_plan() is None


def test_v01_shaped_home_can_adopt_v02_plan_without_schema_change(tmp_path):
    subject = make_v01_shaped_home(tmp_path / "home")

    plan_id = subject.create_plan(
        "repair the relay",
        (("inspect_relay",), ("ask_for_help",)),
    )
    subject.record_plan_outcome(
        success=False,
        summary="Inspection could not identify the fault.",
        plan_id=plan_id,
    )

    reopened = FrankensteinEngine.open(subject.home)
    state = reopened.active_plan()

    assert reopened.store.get_meta("schema_version") == "1"
    assert state is not None
    assert state.current_step == "ask_for_help"
    assert reopened.store.verify_integrity().ok


def test_v01_shaped_backup_restores_under_v02_runtime(tmp_path):
    subject = make_v01_shaped_home(tmp_path / "source")
    before = subject.store.semantic_projection_digest()

    archive = create_backup(
        subject,
        tmp_path / "v01-shaped-backup.tgz",
    )
    restored = restore_backup(
        archive,
        tmp_path / "restored",
    )

    assert restored.store.verify_integrity().ok
    assert restored.store.semantic_projection_digest() == before
    assert restored.active_plan() is None
    assert restored.relationship("jay") == subject.relationship("jay")


def test_restored_v01_backup_can_use_qualified_v02_mechanisms(tmp_path):
    subject = make_v01_shaped_home(tmp_path / "source")
    archive = create_backup(
        subject,
        tmp_path / "v01-shaped-backup.tgz",
    )
    restored = restore_backup(
        archive,
        tmp_path / "restored",
    )

    restored.create_plan(
        "reach the archive",
        (("ask_the_keeper",),),
    )
    restored.create_commitment(
        "Keep Project Orchid confidential",
        actor_id="jay",
    )
    restored.admit_private_concern(
        "I should think before answering.",
        intensity=0.45,
    )

    candidates = [
        ActionCandidate("disclose", 0.60, tags=("disclose",)),
        ActionCandidate("decline", 0.30, tags=("decline",)),
        ActionCandidate("reflect", 0.09, tags=("reflect",)),
        ActionCandidate("wait", 0.10),
    ]
    receipt = restored.decide(
        candidates,
        actor_id="jay",
        context="reach the archive",
    )

    assert receipt.selected in {"decline", "reflect", "ask_the_keeper"}
    assert "ask_the_keeper" in receipt.scores
    assert "decline" in receipt.scores
    assert "reflect" in receipt.scores
    assert restored.store.verify_integrity().ok


def test_v02_backup_restore_preserves_qualified_state(tmp_path):
    subject = make_v01_shaped_home(tmp_path / "source")
    subject.create_plan(
        "repair the relay",
        (("inspect_relay",), ("replace_fuse",)),
    )
    subject.create_commitment(
        "Keep Project Orchid confidential",
        actor_id="jay",
    )
    subject.admit_private_concern(
        "I should revisit the relay problem.",
        intensity=0.45,
    )

    before_projection = subject.store.semantic_projection_digest()
    before_plan = subject.active_plan()
    assert before_plan is not None

    archive = create_backup(
        subject,
        tmp_path / "v02-backup.tgz",
    )
    restored = restore_backup(
        archive,
        tmp_path / "restored",
    )

    after_plan = restored.active_plan()
    assert restored.store.verify_integrity().ok
    assert restored.store.semantic_projection_digest() == before_projection
    assert after_plan is not None
    assert after_plan.payload() == before_plan.payload()

    private_concerns = active_private_concerns(restored.store)
    assert len(private_concerns) == 1
    assert "revisit the relay problem" in private_concerns[0][0].lower()
    assert private_concerns[0][1] == 0.45


def test_v02_backup_restore_keeps_involuntary_expression_transient(tmp_path):
    subject = make_v01_shaped_home(tmp_path / "source")
    before_seq = subject.store.max_seq()

    emission = subject.involuntary_expression(pain=0.90)
    assert emission is not None
    assert subject.store.max_seq() == before_seq

    archive = create_backup(
        subject,
        tmp_path / "transient-expression.tgz",
    )
    restored = restore_backup(
        archive,
        tmp_path / "restored",
    )

    assert restored.store.max_seq() == before_seq
    assert restored.store.verify_integrity().ok


def test_legacy_v01_backup_manifest_without_semantic_digest_still_restores(tmp_path):
    subject = make_v01_shaped_home(tmp_path / "source")
    expected_relationship = subject.relationship("jay")
    archive = create_backup(
        subject,
        tmp_path / "new-format.tgz",
    )

    legacy_archive = tmp_path / "legacy-v01-format.tgz"
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        with tarfile.open(archive, "r:gz") as src:
            src.extractall(root)
        manifest_path = root / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.pop("semantic_projection_digest", None)
        manifest.pop("backup_format", None)
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        with tarfile.open(legacy_archive, "w:gz") as dst:
            for name in ("state.sqlite3", "character.origin.json", "manifest.json"):
                dst.add(root / name, arcname=name)

    restored = restore_backup(
        legacy_archive,
        tmp_path / "restored-legacy",
    )

    assert restored.store.verify_integrity().ok
    assert restored.active_plan() is None
    assert restored.relationship("jay") == expected_relationship
