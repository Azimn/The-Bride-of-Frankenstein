from bride.longitudinal import run_integrated_longitudinal


def test_integrated_longitudinal_candidate_passes_all_trials():
    report = run_integrated_longitudinal()
    failures = [
        trial.to_dict()
        for trial in report.trials
        if not trial.passed
    ]
    assert report.passed, failures


def test_integrated_longitudinal_suite_covers_required_dimensions():
    report = run_integrated_longitudinal()
    ids = {trial.trial_id for trial in report.trials}

    assert {
        "planning-persistence",
        "confidentiality-policy",
        "private-cognition-policy",
        "involuntary-expression",
        "combined-pressure-competition",
        "renderer-swap-invariance",
        "nonperturbing-diagnostic-fork",
        "remember-versus-intrude",
        "developmental-path-divergence",
    } <= ids
