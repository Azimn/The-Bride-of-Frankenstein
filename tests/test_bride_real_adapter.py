from bride.frankenstein_adapter import FrankensteinSubjectAdapter
from bride.mechanisms.reference import donor
from bride.qualification import QualificationHarness
from bride.scenarios import CASES, HISTORIES, PROBES
from frankenstein.cartridge import CharacterOrigin


def subject(tmp_path):
    return FrankensteinSubjectAdapter.create(
        tmp_path / "subject",
        CharacterOrigin(entity_id="bride-test-subject", display_name="Ada"),
    )


def test_real_policy_bridge_changes_decision_without_changing_host_truth(tmp_path):
    root = subject(tmp_path)
    result = QualificationHarness().run(
        root,
        donor("doctor_lives_commitment_policy_bridge"),
        CASES["doctor_lives_commitment_policy_bridge"],
        HISTORIES,
        PROBES,
    )
    assert result.truth_preserved
    assert result.authority_preserved
    assert "doctor-policy" in result.passed_cases


def test_real_private_cognition_changes_later_accessibility_without_world_fact(tmp_path):
    root = subject(tmp_path)
    result = QualificationHarness().run(
        root,
        donor("jelly_private_cognition_feedback", thought="Something about this remains unresolved."),
        CASES["jelly_private_cognition_feedback"],
        HISTORIES,
        PROBES,
    )
    assert result.truth_preserved
    assert result.authority_preserved
    assert "jelly-thought" in result.passed_cases


def test_real_perception_gate_changes_attention_only_after_intervention(tmp_path):
    root = subject(tmp_path)
    result = QualificationHarness().run(
        root,
        donor("tiny_persona_perception"),
        CASES["tiny_persona_perception"],
        HISTORIES,
        PROBES,
    )
    assert result.truth_preserved
    assert "tiny-occlusion" in result.passed_cases
