from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Stimulus:
    stimulus_id: str
    content: str
    modality: str = "vision"
    distance: float = 0.0
    intensity: float = 1.0
    occluded: bool = False


class BoundedPerception:
    """TinyPersona-inspired character-relative perceptual access filter."""

    def __init__(self, *, visual_range: float = 10.0, auditory_range: float = 15.0, attention_capacity: int = 4):
        self.visual_range = visual_range
        self.auditory_range = auditory_range
        self.attention_capacity = max(1, int(attention_capacity))

    def accessible(self, stimuli: tuple[Stimulus, ...]) -> tuple[Stimulus, ...]:
        candidates: list[Stimulus] = []
        for s in stimuli:
            if s.modality == "vision":
                if s.occluded or s.distance > self.visual_range:
                    continue
            elif s.modality == "hearing":
                if s.distance > self.auditory_range:
                    continue
            elif s.distance > max(self.visual_range, self.auditory_range):
                continue
            candidates.append(s)
        candidates.sort(key=lambda s: (-s.intensity, s.distance, s.stimulus_id))
        return tuple(candidates[: self.attention_capacity])
