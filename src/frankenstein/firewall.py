from __future__ import annotations

from .types import SubjectiveFrame


_FORBIDDEN_MARKERS = (
    "source_event_id",
    "event_hash",
    "prev_hash",
    "projection_cursor",
    "raw_score",
    "utility_score",
    "checkpoint_sha",
)


def qualitative_need(name: str, value: float) -> str | None:
    if value <= 0.2:
        return f"{name} feels urgently low"
    if value <= 0.4:
        return f"{name} is tugging at attention"
    if value >= 0.9:
        return f"{name} feels fully settled"
    return None


def qualitative_relationship(values: dict[str, float]) -> str:
    if not values:
        return "This person is not yet well known."
    trust = values.get("trust", 0.0)
    attachment = values.get("attachment", 0.0)
    resentment = values.get("resentment", 0.0)
    fear = values.get("fear", 0.0)
    parts: list[str] = []
    if trust > 0.45:
        parts.append("There is established trust")
    elif trust < -0.35:
        parts.append("Trust is damaged")
    if attachment > 0.45:
        parts.append("The bond matters personally")
    if resentment > 0.35:
        parts.append("Unresolved resentment remains")
    if fear > 0.35:
        parts.append("Some caution or fear is active")
    return ". ".join(parts) + ("." if parts else "The relationship is mixed and still developing.")



def qualitative_affect(values: dict[str, float]) -> tuple[str, ...]:
    out: list[str] = []
    valence = values.get("valence", 0.0)
    arousal = values.get("arousal", 0.0)
    tension = values.get("tension", 0.0)
    if valence > 0.35:
        out.append("The emotional residue is broadly positive")
    elif valence < -0.35:
        out.append("The emotional residue is broadly negative")
    if arousal > 0.45:
        out.append("Activation is elevated")
    elif arousal < -0.45:
        out.append("Activation is unusually low")
    if tension > 0.15:
        out.append("Tension remains active")
    return tuple(out)

def assert_subjective_safe(frame: SubjectiveFrame) -> None:
    text = str(frame.as_prompt_dict())
    lowered = text.lower()
    for marker in _FORBIDDEN_MARKERS:
        if marker in lowered:
            raise ValueError(f"subjective frame leaked machine marker {marker}")
