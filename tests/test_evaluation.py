from frankenstein.evaluation import run_acceptance


def test_acceptance_harness():
    passed = run_acceptance()
    assert len(passed) >= 15
    assert "path-dependence" in passed
    assert "replay-equivalence" in passed
