from dataclasses import asdict

from frankenstein.cartridge import CharacterOrigin
from frankenstein.decision import ActionCandidate
from frankenstein.engine import FrankensteinEngine
from frankenstein.types import EventKind


def engine(tmp_path):
    return FrankensteinEngine(
        tmp_path / "subject",
        CharacterOrigin(
            entity_id="v02-expression-subject",
            display_name="Ada",
        ),
    )


def test_neutral_state_emits_no_involuntary_expression(tmp_path):
    subject = engine(tmp_path)

    assert subject.involuntary_expression(
        pain=0.4,
        surprise=0.7,
    ) is None


def test_high_pain_emits_nonintentional_qualitative_reflex(tmp_path):
    subject = engine(tmp_path)

    emission = subject.involuntary_expression(pain=0.90)

    assert emission is not None
    assert emission.kind == "pain_vocalization"
    assert emission.intentional is False
    assert emission.trigger == "high_pain"
    assert "0.9" not in repr(asdict(emission))


def test_extreme_surprise_generalizes_to_startle_reflex(tmp_path):
    subject = engine(tmp_path)

    emission = subject.involuntary_expression(surprise=0.98)

    assert emission is not None
    assert emission.kind == "startle_vocalization"
    assert emission.intentional is False
    assert emission.trigger == "extreme_surprise"


def test_expression_evaluation_creates_no_canonical_or_noncanonical_event(tmp_path):
    subject = engine(tmp_path)
    before_seq = subject.store.max_seq()

    emission = subject.involuntary_expression(pain=0.90)

    assert emission is not None
    assert subject.store.max_seq() == before_seq
    assert subject.store.verify_integrity().ok


def test_expression_does_not_change_deliberate_decision(tmp_path):
    subject = engine(tmp_path)
    candidates = [
        ActionCandidate("wait", base_utility=0.40),
        ActionCandidate("leave", base_utility=0.20),
    ]

    before = subject.decide(
        candidates,
        context="quiet room",
    )
    emission = subject.involuntary_expression(pain=0.90)
    after = subject.decide(
        candidates,
        context="quiet room",
    )

    assert emission is not None
    assert before.selected == "wait"
    assert after.selected == "wait"


def test_expression_does_not_create_subject_action(tmp_path):
    subject = engine(tmp_path)

    subject.involuntary_expression(pain=0.90)

    actions = [
        event
        for event in subject.store.iter_events(canonical_only=True)
        if event.kind == EventKind.SUBJECT_ACTION.value
    ]
    assert actions == []


def test_expression_does_not_modify_memory_or_prospective_state(tmp_path):
    subject = engine(tmp_path)

    subject.involuntary_expression(
        pain=1.0,
        surprise=1.0,
    )

    with subject.store.connect() as conn:
        memories = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        beliefs = conn.execute("SELECT COUNT(*) FROM beliefs").fetchone()[0]
        commitments = conn.execute("SELECT COUNT(*) FROM commitments").fetchone()[0]
        goals = conn.execute("SELECT COUNT(*) FROM goals").fetchone()[0]
        concerns = conn.execute("SELECT COUNT(*) FROM concerns").fetchone()[0]

    assert memories == 0
    assert beliefs == 0
    assert commitments == 0
    assert goals == 0
    assert concerns == 0


def test_pain_has_deterministic_precedence_when_two_reflexes_are_extreme(tmp_path):
    subject = engine(tmp_path)

    emission = subject.involuntary_expression(
        pain=1.0,
        surprise=1.0,
    )

    assert emission is not None
    assert emission.kind == "pain_vocalization"


def test_out_of_range_inputs_are_bounded_without_exposing_values(tmp_path):
    subject = engine(tmp_path)

    emission = subject.involuntary_expression(
        pain=100.0,
        surprise=-100.0,
    )

    assert emission is not None
    assert asdict(emission) == {
        "kind": "pain_vocalization",
        "intentional": False,
        "trigger": "high_pain",
    }
