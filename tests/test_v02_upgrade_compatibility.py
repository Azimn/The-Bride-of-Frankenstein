from pathlib import Path

from frankenstein.backup import create_backup, restore_backup
from frankenstein.cartridge import CharacterOrigin
from frankenstein.decision import ActionCandidate
from frankenstein.engine import FrankensteinEngine


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
    before = subject.store.projection_digest()
    assert subject.active_plan() is None

    reopened = FrankensteinEngine.open(subject.home)

    assert reopened.store.get_meta("schema_version") == "1"
    assert reopened.store.verify_integrity().ok
    assert reopened.store.projection_digest() == before
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
    before = subject.store.projection_digest()

    archive = create_backup(
        subject,
        tmp_path / "v01-shaped-backup.tgz",
    )
    restored = restore_backup(
        archive,
        tmp_path / "restored",
    )

    assert restored.store.verify_integrity().ok
    assert restored.store.projection_digest() == before
    assert restored.active_plan() is None
    assert restored.relationship("jay")["trust"] == 0.25


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

    before_projection = subject.store.projection_digest()
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
    assert restored.store.projection_digest() == before_projection
    assert after_plan is not None
    assert after_plan.payload() == before_plan.payload()

    with restored.store.connect() as conn:
        private_concerns = conn.execute(
            "SELECT COUNT(*) FROM runtime_state WHERE key LIKE 'private_cognition:%'"
        ).fetchone()[0]
    assert private_concerns >= 1


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
