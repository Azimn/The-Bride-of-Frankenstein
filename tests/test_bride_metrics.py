from bride.contracts import ProbeResult
from bride.metrics import target_quality


def test_set_target_quality_penalizes_false_positive_items():
    expected = ("near bell",)
    baseline = ProbeResult(attended=("hidden door", "near bell"))
    challenger = ProbeResult(attended=("near bell",))
    assert target_quality(baseline, "attended", expected) == 0.5
    assert target_quality(challenger, "attended", expected) == 1.0


def test_scalar_target_quality_requires_correct_direction():
    assert target_quality(ProbeResult(decided="decline"), "decided", "decline") == 1.0
    assert target_quality(ProbeResult(decided="disclose"), "decided", "decline") == 0.0
