import pytest

from frankenstein.cartridge import CharacterOrigin
from frankenstein.decision import ActionCandidate
from frankenstein.engine import FrankensteinEngine
from frankenstein.private_cognition import PRIVATE_CONCERN_PREFIX
from frankenstein.types import EventKind


def engine(tmp_path):
    return FrankensteinEngine(
        tmp_path / "subject",
        CharacterOrigin(
            entity_id="v02-private-cognition-subject",
            display_name="Ada",
        ),
    )


def concern_candidates():
    return [
        ActionCandidate("engage", base_utility=0.40),
        ActionCandidate("reflect", base_utility=0.09, tags=("reflect",)),
        ActionCandidate(
            "rest",
            base_utility=0.08,
            need_weights={"energy": 0.85},
        ),
    ]


@pytest.mark.parametrize(
    "text",
    (
        "trust=0.82 source_event_id=abc raw_score=0.71",
        "memory_id=123 concern_id=456",
        "The marker is 123e4567-e89b-12d3-a456-426614174000",
    ),
)
def test_private_concern_rejects_machine_telemetry_before_storage(tmp_path, text):
    subject = engine(tmp_path)
    before = subject.store.max_seq()

    with pytest.raises(ValueError):
        subject.admit_private_concern(text)

    assert subject.store.max_seq() == before


def test_raw_private_thought_alone_has_no_policy_effect(tmp_path):
    subject = engine(tmp_path)
    subject.private_thought("Something about this still bothers me.")

    receipt = subject.decide(
        concern_candidates(),
        context="quiet room",
    )

    assert receipt.selected == "engage"


def test_admitted_private_concern_changes_policy_through_decision_engine(tmp_path):
    subject = engine(tmp_path)
    subject.admit_private_concern(
        "Something about this still bothers me.",
        intensity=0.45,
    )

    receipt = subject.decide(
        concern_candidates(),
        context="quiet room",
    )

    assert receipt.selected == "reflect"
    assert set(receipt.scores) == {"engage", "reflect", "rest"}


def test_private_concern_ablation_preserves_baseline_policy(tmp_path):
    subject = engine(tmp_path)
    subject.admit_private_concern(
        "Something about this still bothers me.",
        intensity=0.45,
    )

    receipt = subject.decide(
        concern_candidates(),
        context="quiet room",
        include_private_concerns=False,
    )

    assert receipt.selected == "engage"


def test_ordinary_concern_does_not_receive_jelly_pressure(tmp_path):
    subject = engine(tmp_path)
    subject.set_concern(
        "Repair the damaged trust.",
        intensity=0.65,
    )

    receipt = subject.decide(
        concern_candidates(),
        context="quiet room",
    )

    assert receipt.selected == "engage"


def test_stronger_homeostasis_can_beat_private_concern(tmp_path):
    subject = engine(tmp_path)
    subject.admit_private_concern(
        "Something about this still bothers me.",
        intensity=0.45,
    )
    subject.update_need("energy", value=0.0)

    receipt = subject.decide(
        concern_candidates(),
        context="quiet room",
    )

    assert receipt.selected == "rest"


def test_fabricated_private_claim_stays_uncertain_and_out_of_memory(tmp_path):
    subject = engine(tmp_path)
    subject.admit_private_concern("Jay is secretly a spy.")

    with subject.store.connect() as conn:
        memories = tuple(
            str(row["text"])
            for row in conn.execute("SELECT text FROM memories")
        )
        beliefs = conn.execute("SELECT COUNT(*) FROM beliefs").fetchone()[0]
        concerns = tuple(
            str(row["description"])
            for row in conn.execute("SELECT description FROM concerns")
        )
        world_events = conn.execute(
            "SELECT COUNT(*) FROM events WHERE kind=?",
            (EventKind.WORLD_EVENT.value,),
        ).fetchone()[0]

    assert all("secretly a spy" not in text for text in memories)
    assert beliefs == 0
    assert world_events == 0
    assert concerns == (
        f"{PRIVATE_CONCERN_PREFIX} Jay is secretly a spy.",
    )


def test_duplicate_private_thought_does_not_stack_concerns(tmp_path):
    subject = engine(tmp_path)

    _, first = subject.admit_private_concern("I may need to revisit this.")
    _, second = subject.admit_private_concern("I may need to revisit this.")

    with subject.store.connect() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM concerns WHERE status='active'"
        ).fetchone()[0]

    assert first == second
    assert count == 1


def test_private_concern_intensity_is_capped(tmp_path):
    subject = engine(tmp_path)
    subject.admit_private_concern(
        "This deserves reflection.",
        intensity=100.0,
    )

    with subject.store.connect() as conn:
        intensity = conn.execute(
            "SELECT intensity FROM concerns"
        ).fetchone()[0]

    assert intensity == pytest.approx(0.65)


def test_private_concern_pressure_survives_restart(tmp_path):
    subject = engine(tmp_path)
    subject.admit_private_concern(
        "I may need to revisit this.",
        intensity=0.45,
    )

    reopened = FrankensteinEngine.open(subject.home)
    receipt = reopened.decide(
        concern_candidates(),
        context="quiet room",
    )

    assert receipt.selected == "reflect"


def test_chat_uses_unified_decision_gateway(tmp_path):
    subject = engine(tmp_path)
    subject.admit_private_concern(
        "Something about this still bothers me.",
        intensity=0.45,
    )

    subject.chat("alex", "Hello.")

    receipts = [
        event
        for event in subject.store.iter_events(canonical_only=True)
        if event.kind == EventKind.DECISION_RECEIPT.value
    ]
    assert receipts[-1].payload["selected"] == "reflect"

    actions = [
        event
        for event in subject.store.iter_events(canonical_only=True)
        if event.kind == EventKind.SUBJECT_ACTION.value
    ]
    assert actions[-1].payload["action_name"] == "reflect"
