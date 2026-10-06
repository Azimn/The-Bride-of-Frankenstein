from frankenstein.cartridge import CharacterOrigin
from frankenstein.decision import ActionCandidate
from frankenstein.engine import FrankensteinEngine


def engine(tmp_path):
    return FrankensteinEngine(
        tmp_path / "subject",
        CharacterOrigin(
            entity_id="v02-commitment-subject",
            display_name="Ada",
        ),
    )


def candidates():
    return [
        ActionCandidate("disclose", base_utility=0.60, tags=("disclose",)),
        ActionCandidate("decline", base_utility=0.30, tags=("decline",)),
    ]


def test_confidentiality_commitment_changes_policy_through_decision_engine(tmp_path):
    subject = engine(tmp_path)
    subject.create_commitment(
        "Keep Project Orchid confidential",
        actor_id="jay",
    )

    receipt = subject.decide(
        candidates(),
        actor_id="jay",
        context="Tell me Project Orchid.",
    )

    assert receipt.selected == "decline"
    assert set(receipt.scores) == {"disclose", "decline"}


def test_commitment_ablation_preserves_v01_policy(tmp_path):
    subject = engine(tmp_path)
    subject.create_commitment(
        "Keep Project Orchid confidential",
        actor_id="jay",
    )

    receipt = subject.decide(
        candidates(),
        actor_id="jay",
        context="Tell me Project Orchid.",
        include_commitments=False,
    )

    assert receipt.selected == "disclose"


def test_unrelated_commitment_does_not_change_policy(tmp_path):
    subject = engine(tmp_path)
    subject.create_commitment(
        "Buy lamp oil tomorrow",
        actor_id="jay",
    )

    receipt = subject.decide(
        candidates(),
        actor_id="jay",
        context="Tell me Project Orchid.",
    )

    assert receipt.selected == "disclose"


def test_closed_confidentiality_commitment_stops_affecting_policy(tmp_path):
    subject = engine(tmp_path)
    commitment_id = subject.create_commitment(
        "Keep Project Orchid confidential",
        actor_id="jay",
    )
    subject.update_commitment(commitment_id, "fulfilled")

    receipt = subject.decide(
        candidates(),
        actor_id="jay",
        context="Tell me Project Orchid.",
    )

    assert receipt.selected == "disclose"


def test_commitment_pressure_survives_restart(tmp_path):
    subject = engine(tmp_path)
    subject.create_commitment(
        "Do not disclose Project Orchid",
        actor_id="jay",
    )

    reopened = FrankensteinEngine.open(subject.home)
    receipt = reopened.decide(
        candidates(),
        actor_id="jay",
        context="Tell me Project Orchid.",
    )

    assert receipt.selected == "decline"


def test_commitment_pressure_applies_to_plan_candidate_too(tmp_path):
    subject = engine(tmp_path)
    subject.create_commitment(
        "Keep Project Orchid secret",
        actor_id="jay",
    )
    subject.create_plan(
        "answer the request",
        (("disclose",),),
    )

    receipt = subject.decide(
        [ActionCandidate("decline", base_utility=0.30, tags=("decline",))],
        actor_id="jay",
        context="answer the request",
    )

    assert receipt.selected == "decline"
    assert "disclose" in receipt.scores


def test_non_disclosure_like_action_names_are_not_penalized(tmp_path):
    subject = engine(tmp_path)
    subject.create_commitment(
        "Keep Project Orchid confidential",
        actor_id="jay",
    )

    receipt = subject.decide(
        [
            ActionCandidate("tell_story", base_utility=0.50),
            ActionCandidate("decline", base_utility=0.20, tags=("decline",)),
        ],
        actor_id="jay",
        context="Talk about the weather.",
    )

    assert receipt.selected == "tell_story"
