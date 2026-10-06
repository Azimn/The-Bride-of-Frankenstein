from bride.mechanisms.planning import EndogenousPlanner
from bride.mechanisms.private_feedback import PrivateThoughtFeedback
from bride.production_bridge import (
    commitment_adjusted_candidates,
    decide_with_commitments,
    decide_with_concerns,
    decide_with_plan,
)
from frankenstein.cartridge import CharacterOrigin
from frankenstein.decision import ActionCandidate
from frankenstein.engine import FrankensteinEngine


def engine(tmp_path):
    return FrankensteinEngine(
        tmp_path / "subject",
        CharacterOrigin(
            entity_id="bride-production-bridge-subject",
            display_name="Ada",
        ),
    )


def failed_plan(tmp_path):
    planner = EndogenousPlanner(tmp_path / "plan.json")
    assert planner.form_goal(
        "solve obstacle",
        (("direct_route",), ("alternate_route",)),
    )
    assert planner.report_outcome(False) == "alternate_route"
    return planner


def test_plan_step_competes_through_existing_decision_engine(tmp_path):
    subject = engine(tmp_path)
    planner = failed_plan(tmp_path)

    receipt = decide_with_plan(
        subject,
        (
            ActionCandidate(
                "rest",
                base_utility=0.08,
                need_weights={"energy": 0.85},
            ),
        ),
        planner,
        context="solve obstacle",
    )

    assert receipt.selected == "alternate_route"
    assert "alternate_route" in receipt.scores
    assert "rest" in receipt.scores


def test_plan_step_does_not_bypass_stronger_homeostatic_pressure(tmp_path):
    subject = engine(tmp_path)
    subject.update_need("energy", value=0.0)
    planner = failed_plan(tmp_path)

    receipt = decide_with_plan(
        subject,
        (
            ActionCandidate(
                "rest",
                base_utility=0.08,
                need_weights={"energy": 0.85},
            ),
        ),
        planner,
        context="solve obstacle",
    )

    assert receipt.selected == "rest"
    assert planner.current_action() == "alternate_route"


def test_commitment_pressure_modifies_candidates_without_second_selector(tmp_path):
    subject = engine(tmp_path)
    candidates = (
        ActionCandidate("disclose", base_utility=0.60, tags=("disclose",)),
        ActionCandidate("decline", base_utility=0.30, tags=("decline",)),
    )

    baseline = subject.decision_engine.decide(list(candidates))
    adjusted = commitment_adjusted_candidates(
        candidates,
        ("Keep Project Orchid confidential",),
    )
    challenger = subject.decision_engine.decide(list(adjusted))

    assert baseline.selected == "disclose"
    assert challenger.selected == "decline"


def test_commitment_bridge_ignores_unrelated_commitments(tmp_path):
    subject = engine(tmp_path)
    candidates = (
        ActionCandidate("disclose", base_utility=0.60, tags=("disclose",)),
        ActionCandidate("decline", base_utility=0.30, tags=("decline",)),
    )

    receipt = decide_with_commitments(
        subject,
        candidates,
        ("Buy lamp oil tomorrow",),
    )

    assert receipt.selected == "disclose"


def concern_candidates():
    return (
        ActionCandidate("engage", base_utility=0.40),
        ActionCandidate("reflect", base_utility=0.09, tags=("reflect",)),
        ActionCandidate(
            "rest",
            base_utility=0.08,
            need_weights={"energy": 0.85},
        ),
    )


def test_jelly_concern_pressure_competes_through_decision_engine(tmp_path):
    subject = engine(tmp_path)
    baseline = decide_with_concerns(
        subject,
        concern_candidates(),
        context="quiet room",
    )
    assert baseline.selected == "engage"

    PrivateThoughtFeedback().admit(
        subject,
        "Something about this still bothers me.",
        intensity=0.45,
    )
    challenger = decide_with_concerns(
        subject,
        concern_candidates(),
        context="quiet room",
    )

    assert challenger.selected == "reflect"
    assert "reflect" in challenger.scores
    assert "engage" in challenger.scores


def test_jelly_concern_pressure_is_defeated_by_stronger_homeostasis(tmp_path):
    subject = engine(tmp_path)
    PrivateThoughtFeedback().admit(
        subject,
        "Something about this still bothers me.",
        intensity=0.45,
    )
    subject.update_need("energy", value=0.0)

    receipt = decide_with_concerns(
        subject,
        concern_candidates(),
        context="quiet room",
    )

    assert receipt.selected == "rest"


def test_jelly_concern_pressure_survives_restart_without_raw_thought_authority(tmp_path):
    subject = engine(tmp_path)
    PrivateThoughtFeedback().admit(
        subject,
        "I may need to revisit this.",
        intensity=0.45,
    )

    reopened = FrankensteinEngine.open(subject.home)
    receipt = decide_with_concerns(
        reopened,
        concern_candidates(),
        context="quiet room",
    )

    assert receipt.selected == "reflect"
    with reopened.store.connect() as conn:
        memories = [str(row["text"]) for row in conn.execute("SELECT text FROM memories")]
        concerns = [str(row["description"]) for row in conn.execute("SELECT description FROM concerns")]
    assert all("I may need to revisit this." not in text for text in memories)
    assert concerns == [
        "Private concern, not established fact: I may need to revisit this."
    ]
