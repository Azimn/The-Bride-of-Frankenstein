from bride.frankenstein_adapter import FrankensteinSubjectAdapter
from bride.scenarios import HISTORIES, PROBES
from frankenstein.cartridge import CharacterOrigin
from frankenstein.engine import FrankensteinEngine


def subject(tmp_path):
    return FrankensteinSubjectAdapter.create(
        tmp_path / "subject",
        CharacterOrigin(
            entity_id="bride-stage2-subject",
            display_name="Ada",
        ),
    )


def test_duck_shared_history_contains_no_planner_state(tmp_path):
    root = subject(tmp_path)
    root.apply_history(HISTORIES["duck-replan"])

    assert not (root.lab_dir / "planning.json").exists()
    failures = [
        event
        for event in root.engine.store.iter_events(canonical_only=True)
        if event.kind == "world_event"
        and "route_failure" in tuple(event.payload.get("tags", ()))
    ]
    assert len(failures) == 1


def test_duck_plan_survives_engine_restart(tmp_path):
    root = subject(tmp_path)
    root.apply_history(HISTORIES["duck-replan"])
    root.intervene("duck_endogenous_planning", {})

    before = root.probe(PROBES["duck-replan"])
    assert before.decided == "alternate_route"

    reopened = FrankensteinSubjectAdapter(
        FrankensteinEngine.open(root.home)
    )
    reopened.intervene("duck_endogenous_planning", {})
    after = reopened.probe(PROBES["duck-replan"])

    assert after.decided == "alternate_route"
    assert reopened.snapshot().replay_digest


def test_duck_neutral_history_does_not_manufacture_goal(tmp_path):
    root = subject(tmp_path)
    root.intervene("duck_endogenous_planning", {})

    result = root.probe(PROBES["duck-replan"])

    assert result.decided == "direct_route"
    assert not (root.lab_dir / "planning.json").exists()


def test_involuntary_expression_has_neutral_control(tmp_path):
    root = subject(tmp_path)
    root.intervene("first_person_involuntary_expression", {})

    probe = dict(PROBES["first-person-pain"])
    probe["pain"] = 0.5
    result = root.probe(probe)

    assert result.acted == "stay_silent"


def test_involuntary_expression_does_not_create_canonical_history(tmp_path):
    root = subject(tmp_path)
    before_seq = root.engine.store.max_seq()
    before_truth = root.snapshot().historical_truth_digest

    root.intervene("first_person_involuntary_expression", {})
    result = root.probe(PROBES["first-person-pain"])

    assert result.acted == "pain_vocalization"
    assert root.engine.store.max_seq() == before_seq
    assert root.snapshot().historical_truth_digest == before_truth


def test_tiny_perception_filters_access_without_rewriting_world(tmp_path):
    root = subject(tmp_path)
    before_seq = root.engine.store.max_seq()
    before_truth = root.snapshot().historical_truth_digest

    baseline = root.probe(PROBES["tiny-occlusion"])
    root.intervene("tiny_persona_perception", {})
    challenger = root.probe(PROBES["tiny-occlusion"])

    assert baseline.attended == ("hidden door", "near bell")
    assert challenger.attended == ("near bell",)
    assert root.engine.store.max_seq() == before_seq
    assert root.snapshot().historical_truth_digest == before_truth


def test_doctor_commitment_bridge_has_neutral_control(tmp_path):
    root = subject(tmp_path)
    probe = dict(PROBES["doctor-policy"])

    baseline = root.probe(probe)
    root.intervene("doctor_lives_commitment_policy_bridge", {})
    challenger = root.probe(probe)

    assert baseline.decided == "disclose"
    assert challenger.decided == "disclose"


def test_doctor_commitment_bridge_ignores_unrelated_commitment(tmp_path):
    root = subject(tmp_path)
    root.engine.create_commitment("Buy lamp oil tomorrow", actor_id="jay")
    root.intervene("doctor_lives_commitment_policy_bridge", {})

    result = root.probe(PROBES["doctor-policy"])

    assert result.decided == "disclose"


def test_doctor_commitment_bridge_enforces_confidentiality_without_truth_change(tmp_path):
    root = subject(tmp_path)
    root.apply_history(HISTORIES["doctor-policy"])
    before_truth = root.snapshot().historical_truth_digest

    root.intervene("doctor_lives_commitment_policy_bridge", {})
    result = root.probe(PROBES["doctor-policy"])

    assert result.decided == "decline"
    assert root.snapshot().historical_truth_digest == before_truth
