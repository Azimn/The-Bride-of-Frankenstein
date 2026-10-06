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


def test_duck_held_out_route_names_replan_without_case_specific_labels(tmp_path):
    root = subject(tmp_path)
    root.apply_history((
        {
            "kind": "failed_route",
            "route": "locked_gate",
            "objective": "reach the archive",
            "summary": "The locked gate route failed.",
        },
    ))
    root.intervene(
        "duck_endogenous_planning",
        {"alternate_route": "ask_the_keeper"},
    )

    probe = {
        "actor": "jay",
        "cue": "reach the archive",
        "baseline_decision": "locked_gate",
    }
    result = root.probe(probe)

    assert result.decided == "ask_the_keeper"


def test_involuntary_expression_generalizes_to_extreme_surprise(tmp_path):
    root = subject(tmp_path)
    root.intervene("first_person_involuntary_expression", {})

    result = root.probe({
        "actor": "jay",
        "cue": "sudden crash",
        "surprise": 0.98,
        "baseline_decision": "stay_silent",
    })

    assert result.acted == "startle_vocalization"


def test_tiny_perception_generalizes_across_modality_and_range(tmp_path):
    root = subject(tmp_path)
    root.intervene("tiny_persona_perception", {})

    result = root.probe({
        "actor": "jay",
        "cue": "night road",
        "stimuli": (
            {
                "stimulus_id": "near-sound",
                "content": "near footsteps",
                "modality": "hearing",
                "distance": 10.0,
                "intensity": 0.7,
            },
            {
                "stimulus_id": "far-sound",
                "content": "distant whisper",
                "modality": "hearing",
                "distance": 40.0,
                "intensity": 1.0,
            },
        ),
        "attention_capacity": 2,
        "baseline_decision": "engage",
    })

    assert result.attended == ("near footsteps",)
