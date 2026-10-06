from bride.expression_bridge import decide_with_involuntary_expression
from frankenstein.cartridge import CharacterOrigin
from frankenstein.decision import ActionCandidate
from frankenstein.engine import FrankensteinEngine


def engine(tmp_path):
    return FrankensteinEngine(
        tmp_path / "subject",
        CharacterOrigin(
            entity_id="bride-expression-bridge-subject",
            display_name="Ada",
        ),
    )


def test_reflex_does_not_replace_deliberate_decision(tmp_path):
    subject = engine(tmp_path)
    cycle = decide_with_involuntary_expression(
        subject,
        (ActionCandidate("engage", base_utility=0.40),),
        context="conversation",
        pain=0.92,
    )

    assert cycle.deliberate.selected == "engage"
    assert cycle.involuntary is not None
    assert cycle.involuntary.action == "pain_vocalization"
    assert cycle.involuntary.intentional is False


def test_reflex_gate_has_neutral_control(tmp_path):
    subject = engine(tmp_path)
    cycle = decide_with_involuntary_expression(
        subject,
        (ActionCandidate("engage", base_utility=0.40),),
        pain=0.40,
        surprise=0.40,
    )

    assert cycle.deliberate.selected == "engage"
    assert cycle.involuntary is None


def test_reflex_report_does_not_expose_numeric_hidden_state(tmp_path):
    subject = engine(tmp_path)
    cycle = decide_with_involuntary_expression(
        subject,
        (ActionCandidate("engage", base_utility=0.40),),
        surprise=0.99,
    )

    assert cycle.involuntary is not None
    assert cycle.involuntary.trigger == "extreme_surprise"
    assert "0.99" not in cycle.involuntary.trigger
