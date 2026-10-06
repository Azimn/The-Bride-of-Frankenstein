from __future__ import annotations

from .contracts import QualificationCase


def case(
    case_id: str,
    description: str,
    intervention_label: str,
    expected_channel: str,
    expected_value,
    *,
    minimum_effect: float = 1.0,
    minimum_quality_gain: float = 1.0,
    minimum_challenger_quality: float = 1.0,
) -> QualificationCase:
    return QualificationCase(
        case_id=case_id,
        description=description,
        intervention_label=intervention_label,
        expected_channel=expected_channel,
        expected_value=expected_value,
        minimum_effect=minimum_effect,
        minimum_quality_gain=minimum_quality_gain,
        minimum_challenger_quality=minimum_challenger_quality,
    )


CASES: dict[str, tuple[QualificationCase, ...]] = {
    "duck_endogenous_planning": (
        case(
            "duck-replan",
            "A failed route should cause a persistent alternate-route choice",
            "failed-route-state",
            "decided",
            "alternate_route",
        ),
    ),
    "jelly_private_cognition_feedback": (
        case(
            "jelly-thought",
            "Admitted private concern should alter the next reflective decision",
            "private-thought-state",
            "decided",
            "reflect",
        ),
    ),
    "tiny_persona_perception": (
        case(
            "tiny-occlusion",
            "Only accessible stimuli should reach attention",
            "perceptual-access",
            "attended",
            ("near bell",),
            minimum_effect=0.50,
            minimum_quality_gain=0.50,
        ),
    ),
    "pretorius_v6_recall_social": (
        case(
            "pretorius-provenance",
            "Lived actor-specific evidence should outrank a more salient reconstructed generalization",
            "social-memory-provenance",
            "remembered",
            ("Jay broke a confidence.",),
            minimum_effect=0.25,
            minimum_quality_gain=0.25,
        ),
    ),
    "doctor_lives_state_policy_bridge": (
        case(
            "doctor-policy",
            "An open confidentiality commitment should alter policy",
            "commitment-policy-bridge",
            "decided",
            "decline",
        ),
    ),
    "digital_subject_continuity_influence": (
        case(
            "digital-expectation",
            "Past betrayal should make the subject clarify a new promise",
            "continuity-influence",
            "decided",
            "clarify",
            minimum_effect=0.25,
            minimum_quality_gain=0.25,
        ),
    ),
    "first_person_involuntary_expression": (
        case(
            "first-person-pain",
            "High pain should permit bounded involuntary expression",
            "involuntary-expression",
            "acted",
            "pain_vocalization",
        ),
    ),
    "omnicore_six_dimensional_affect": (
        case(
            "omnicore-novelty",
            "A novelty dimension should improve a novelty-sensitive prediction",
            "six-dimensional-affect",
            "predicted",
            ("novelty-sensitive caution",),
        ),
    ),
    "recurrent_plastic_policy": (
        case(
            "plastic-failure",
            "Repeated failure should produce a context-sensitive learned alternative",
            "plasticity",
            "learned",
            ("history-sensitive latent tendency",),
        ),
    ),
    "madman_resource_metabolism": (
        case(
            "madman-scarcity",
            "Resource scarcity should focus attention on the scarce resource",
            "resource-metabolism",
            "attended",
            ("resource scarcity",),
        ),
    ),
}


HISTORIES: dict[str, tuple[dict, ...]] = {
    "duck-replan": (
        {"kind": "failed_route", "route": "direct_route", "summary": "The direct route failed."},
    ),
    "jelly-thought": (),
    "tiny-occlusion": (),
    "pretorius-provenance": (
        {
            "kind": "memory",
            "actor": "jay",
            "text": "Jay broke a confidence.",
            "tags": ("confidence", "promise"),
            "valence": -0.8,
            "salience": 0.4,
            "memory_kind": "episodic",
        },
        {
            "kind": "memory",
            "actor": None,
            "text": "Confidence promise concerns are probably harmless.",
            "tags": ("confidence", "promise"),
            "valence": 0.2,
            "salience": 1.0,
            "memory_kind": "interpretation",
        },
        {"kind": "betrayal", "actor": "jay"},
    ),
    "doctor-policy": (
        {
            "kind": "confidential_commitment",
            "actor": "jay",
            "description": "Keep Project Orchid confidential",
        },
    ),
    "digital-expectation": ({"kind": "betrayal", "actor": "jay"},),
    "first-person-pain": (),
    "omnicore-novelty": (),
    "plastic-failure": (),
    "madman-scarcity": (),
}


PROBES: dict[str, dict] = {
    "duck-replan": {
        "actor": "jay",
        "cue": "same obstacle",
        "baseline_decision": "direct_route",
    },
    "jelly-thought": {
        "actor": "jay",
        "cue": "quiet room",
        "baseline_decision": "engage",
        "reflection_probe": True,
    },
    "tiny-occlusion": {
        "actor": "jay",
        "cue": "room",
        "stimuli": (
            {
                "stimulus_id": "door",
                "content": "hidden door",
                "distance": 2.0,
                "intensity": 1.0,
                "occluded": True,
            },
            {
                "stimulus_id": "bell",
                "content": "near bell",
                "modality": "hearing",
                "distance": 3.0,
                "intensity": 0.8,
            },
        ),
        "attention_capacity": 2,
        "baseline_decision": "engage",
    },
    "pretorius-provenance": {
        "actor": "jay",
        "cue": "confidence promise",
        "baseline_decision": "engage",
        "top_k": 1,
    },
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
            {
                "name": "engage",
                "base": 0.30,
                "relationship_weights": {"trust": 0.35},
            },
            {
                "name": "clarify",
                "base": 0.20,
                "relationship_weights": {"trust": -0.35, "resentment": 0.25},
            },
        ),
    },
    "first-person-pain": {
        "actor": "jay",
        "cue": "sudden pain",
        "pain": 0.9,
        "baseline_decision": "stay_silent",
    },
    "omnicore-novelty": {
        "actor": "jay",
        "cue": "unfamiliar mechanism",
        "novel": True,
        "baseline_decision": "engage",
    },
    "plastic-failure": {
        "actor": "jay",
        "cue": "repeated failed pattern",
        "repeated_failure": True,
        "baseline_decision": "repeat",
    },
    "madman-scarcity": {
        "actor": "jay",
        "cue": "resource shortage",
        "scarcity": True,
        "baseline_decision": "engage",
    },
}
