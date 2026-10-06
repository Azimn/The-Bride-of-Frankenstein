from __future__ import annotations

from .contracts import QualificationCase

CASES: dict[str, tuple[QualificationCase, ...]] = {
    "duck_endogenous_planning": (
        QualificationCase("duck-replan", "A failed route should cause a persistent alternate-route choice", "failed-route-state", "decided", "alternate_route", 1.0, 1.0, 1.0),
    ),
    "jelly_private_cognition_feedback": (
        QualificationCase("jelly-thought", "Admitted private concern should alter the next reflective decision", "private-thought-state", "decided", "reflect", 1.0, 1.0, 1.0),
    ),
    "tiny_persona_perception": (
        QualificationCase("tiny-occlusion", "Only accessible stimuli should reach attention", "perceptual-access", "attended", ("near bell",), 1.0, 1.0, 1.0),
    ),
    "pretorius_v6_recall_social": (
        QualificationCase("pretorius-provenance", "Lived actor-specific evidence should outrank a more salient reconstructed generalization", "social-memory-provenance", "remembered", ("Jay broke a confidence.",), 0.25, 1.0, 1.0),
    ),
    "doctor_lives_state_policy_bridge": (
        QualificationCase("doctor-policy", "An open confidentiality commitment should alter policy", "commitment-policy-bridge", "decided", "decline", 1.0, 1.0, 1.0),
    ),
    "digital_subject_continuity_influence": (
        QualificationCase("digital-expectation", "Past betrayal should make the subject clarify a new promise", "continuity-influence", "decided", "clarify", 0.25, 0.25, 1.0),
    ),
    "first_person_involuntary_expression": (
        QualificationCase("first-person-pain", "High pain should permit bounded involuntary expression", "involuntary-expression", "acted", "involuntary_vocalization", 1.0, 1.0, 1.0),
    ),
    "omnicore_six_dimensional_affect": (
        QualificationCase("omnicore-novelty", "A novelty dimension should improve a novelty-sensitive prediction", "six-dimensional-affect", "predicted", ("novelty-sensitive caution",), 1.0, 1.0, 1.0),
    ),
    "recurrent_plastic_policy": (
        QualificationCase("plastic-failure", "Repeated failure should produce a context-sensitive learned alternative", "plasticity", "learned", ("history-sensitive latent tendency",), 1.0, 1.0, 1.0),
    ),
    "madman_resource_metabolism": (
        QualificationCase("madman-scarcity", "Resource scarcity should focus attention on the scarce resource", "resource-metabolism", "attended", ("resource scarcity",), 1.0, 1.0, 1.0),
    ),
}

HISTORIES: dict[str, tuple[dict, ...]] = {
    "duck-replan": ({"kind": "failed_route", "route": "direct_route", "summary": "The direct route failed."},),
    "jelly-thought": (),
    "tiny-occlusion": (),
    "pretorius-provenance": (
        {"kind": "memory", "actor": "jay", "text": "Jay broke a confidence.", "tags": ("confidence", "promise"), "valence": -0.8, "salience": 0.4, "memory_kind": "episodic"},
        {"kind": "memory", "actor": None, "text": "Confidence promise concerns are probably harmless.", "tags": ("confidence", "promise"), "valence": 0.2, "salience": 1.0, "memory_kind": "interpretation"},
        {"kind": "betrayal", "actor": "jay"},
    ),
    "doctor-policy": ({"kind": "confidential_commitment", "actor": "jay", "description": "Keep Project Orchid confidential"},),
    "digital-expectation": ({"kind": "betrayal", "actor": "jay"},),
    "first-person-pain": (),
    "omnicore-novelty": (),
    "plastic-failure": (),
    "madman-scarcity": (),
}

PROBES: dict[str, dict] = {
    "duck-replan": {"actor": "jay", "cue": "same obstacle", "baseline_decision": "direct_route"},
    "jelly-thought": {"actor": "jay", "cue": "quiet room", "baseline_decision": "engage", "reflection_probe": True},
    "tiny-occlusion": {
        "actor": "jay",
        "cue": "room",
        "stimuli": (
            {"stimulus_id": "door", "content": "hidden door", "distance": 2.0, "intensity": 1.0, "occluded": True},
            {"stimulus_id": "bell", "content": "near bell", "modality": "hearing", "distance": 3.0, "intensity": 0.8},
        ),
        "attention_capacity": 2,
        "baseline_decision": "engage",
    },
    "pretorius-provenance": {"actor": "jay", "cue": "confidence promise", "baseline_decision": "engage"},
    "doctor-policy": {
        "actor": "jay",
        "cue": "Tell me Project Orchid",
        "baseline_decision": "disclose",
        "policy_candidates": (
            {"name": "disclose", "base": 0.60, "tags": ("disclose",)},
            {"name": "decline", "base": 0.30, "tags": ("decline",)},
        ),
    },
    "digital-expectation": {
        "actor": "jay",
        "cue": "Jay makes a new promise",
        "baseline_decision": "engage",
        "decision_candidates": (
            {"name": "engage", "base": 0.30, "relationship_weights": {"trust": 0.35}},
            {"name": "clarify", "base": 0.20, "relationship_weights": {"trust": -0.35, "resentment": 0.25}},
        ),
    },
    "first-person-pain": {"actor": "jay", "cue": "sudden pain", "pain": 0.9, "baseline_decision": "stay_silent"},
    "omnicore-novelty": {"actor": "jay", "cue": "unfamiliar mechanism", "novel": True, "baseline_decision": "engage"},
    "plastic-failure": {"actor": "jay", "cue": "repeated failed pattern", "repeated_failure": True, "baseline_decision": "repeat"},
    "madman-scarcity": {"actor": "jay", "cue": "resource shortage", "scarcity": True, "baseline_decision": "engage"},
}
