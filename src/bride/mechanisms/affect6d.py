from __future__ import annotations

from dataclasses import dataclass


def _clamp(v: float) -> float:
    return max(-1.0, min(1.0, float(v)))


@dataclass(frozen=True)
class Affect6D:
    valence: float = 0.0
    arousal: float = 0.0
    dominance: float = 0.0
    agency: float = 0.0
    fidelity: float = 0.0
    novelty: float = 0.0

    def updated(self, **deltas: float) -> "Affect6D":
        known = set(self.__dataclass_fields__)
        unknown = set(deltas) - known
        if unknown:
            raise ValueError("unknown 6D affect axes: " + ", ".join(sorted(unknown)))
        values = {name: _clamp(getattr(self, name) + float(deltas.get(name, 0.0))) for name in known}
        return Affect6D(**values)

    def caution_pressure(self) -> float:
        return _clamp(0.35 * self.novelty - 0.20 * self.dominance - 0.15 * self.agency)
