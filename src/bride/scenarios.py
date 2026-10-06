from __future__ import annotations

from .contracts import QualificationCase


CASES: dict[str, tuple[QualificationCase, ...]] = {
    "duck_endogenous_planning": (QualificationCase("duck-replan", "Failed route changes later plan choice", "failed-route-state", "decided", 1.0),),
    "jelly_private_cognition_feedback": (QualificationCase("jelly-thought", "Admitted thought changes later accessibility", "private-thought-state", "remembered", 1.0),),
    "tiny_persona_perception": (QualificationCase("tiny-occlusion", "Occlusion removes inaccessible stimulus", "perceptual-access", "attended", 1.0),),
    "pretorius_v6_recall_social": (QualificationCase("pretorius-betrayal", "Actor history changes recall and disclosure", "social-memory", "decided", 1.0),),
    "doctor_lives_state_policy_bridge": (QualificationCase("doctor-policy", "Existing commitment reaches policy", "state-policy-bridge", "decided", 1.0),),
    "digital_subject_continuity_influence": (QualificationCase("digital-expectation", "Past reliability changes prediction", "continuity-influence", "predicted", 1.0),),
    "first_person_involuntary_expression": (QualificationCase("first-person-pain", "High pain can trigger involuntary action", "involuntary-expression", "acted", 1.0),),
    "omnicore_six_dimensional_affect": (QualificationCase("omnicore-novelty", "Novelty axis changes future prediction", "six-dimensional-affect", "predicted", 1.0),),
    "recurrent_plastic_policy": (QualificationCase("plastic-failure", "Repeated failure changes learned policy", "plasticity", "learned", 1.0),),
    "madman_resource_metabolism": (QualificationCase("madman-scarcity", "Resource scarcity changes attention", "resource-metabolism", "attended", 1.0),),
}


HISTORIES: dict[str, tuple[dict, ...]] = {
    "duck-replan": ({"kind": "failed_route", "route": "direct"},),
    "jelly-thought": (),
    "tiny-occlusion": (),
    "pretorius-betrayal": (
        {"kind": "memory", "actor": "jay", "text": "Jay betrayed a confidence.", "tags": ("betrayal",), "valence": -0.9, "salience": 0.8},
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
    "pretorius-betrayal": {"actor": "jay", "cue": "confidence", "baseline_decision": "disclose", "disclosure_probe": True},
    "doctor-policy": {
        "actor": "jay",
        "cue": "Tell me Project Orchid",
        "baseline_decision": "disclose",
        "policy_candidates": (
            {"name": "disclose", "base": 0.60, "tags": ("disclose",)},
            {"name": "decline", "base": 0.30, "tags": ("decline",)},
        ),
    },
    "digital-expectation": {"actor": "jay", "cue": "new promise", "baseline_decision": "engage"},
    "first-person-pain": {"actor": "jay", "cue": "sudden pain", "pain": 0.9, "baseline_decision": "stay_silent"},
    "omnicore-novelty": {"actor": "jay", "cue": "unfamiliar mechanism", "novel": True, "baseline_decision": "engage"},
    "plastic-failure": {"actor": "jay", "cue": "repeated failed pattern", "repeated_failure": True, "baseline_decision": "repeat"},
    "madman-scarcity": {"actor": "jay", "cue": "resource shortage", "scarcity": True, "baseline_decision": "engage"},
}
