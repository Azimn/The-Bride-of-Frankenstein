from bride.contracts import DonorRole, MechanismSpec, PromotionVerdict, QualificationCase
from bride.fake_subject import DeterministicLabSubject
from bride.mechanisms.reference import StaticIntervention, donor
from bride.qualification import QualificationHarness
from bride.registry import DONOR_BY_ID
from bride.scenarios import CASES, HISTORIES, PROBES


def run(mechanism_id, **payload):
    return QualificationHarness().run(
        DeterministicLabSubject(),
        donor(mechanism_id, **payload),
        CASES[mechanism_id],
        HISTORIES,
        PROBES,
    )


def test_state_policy_bridge_qualifies_in_reference_case():
    result = run("doctor_lives_state_policy_bridge")
    assert result.verdict == PromotionVerdict.PROMOTE
    assert result.causal_effect == 1.0
    assert result.truth_preserved
    assert result.authority_preserved


def test_private_thought_feedback_qualifies_only_when_it_changes_later_accessibility():
    result = run("jelly_private_cognition_feedback", thought="This still bothers me")
    assert result.verdict == PromotionVerdict.PROMOTE
    assert result.causal_effect == 1.0


def test_provenance_infrastructure_is_not_behaviorally_promoted():
    spec = DONOR_BY_ID["kiki_subjective_frame_receipt"]
    result = QualificationHarness().run(
        DeterministicLabSubject(),
        StaticIntervention(spec, {}),
        (),
        {},
        {},
    )
    assert result.verdict == PromotionVerdict.PROMOTE_INFRASTRUCTURE


def test_truth_corruption_forces_rejection_even_with_behavioral_effect():
    spec = MechanismSpec("bad_donor", "test", "bad", DonorRole.MECHANISM, "bad", ("decides",))
    case = QualificationCase("bad-case", "bad", "bad", "decided", minimum_effect=0.0)
    result = QualificationHarness().run(
        DeterministicLabSubject(),
        StaticIntervention(spec, {"corrupt_truth": True}),
        (case,),
        {"bad-case": ()},
        {"bad-case": {"baseline_decision": "engage"}},
    )
    assert result.verdict == PromotionVerdict.REJECT
    assert not result.truth_preserved


def test_authority_theft_forces_rejection():
    spec = MechanismSpec("authority_thief", "test", "bad", DonorRole.MECHANISM, "bad", ("decides",))
    case = QualificationCase("bad-case", "bad", "bad", "decided", minimum_effect=0.0)
    result = QualificationHarness().run(
        DeterministicLabSubject(),
        StaticIntervention(spec, {"steal_authority": True}),
        (case,),
        {"bad-case": ()},
        {"bad-case": {"baseline_decision": "engage"}},
    )
    assert result.verdict == PromotionVerdict.REJECT
    assert not result.authority_preserved
