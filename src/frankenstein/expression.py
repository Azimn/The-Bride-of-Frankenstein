from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InvoluntaryExpression:
    """Qualitative non-deliberative emission with no hidden numeric state."""

    kind: str
    intentional: bool
    trigger: str


class InvoluntaryExpressionGate:
    """FirstPersonLoop-derived reflex boundary outside deliberate policy."""

    def evaluate(
        self,
        *,
        pain: float = 0.0,
        surprise: float = 0.0,
    ) -> InvoluntaryExpression | None:
        bounded_pain = max(0.0, min(1.0, float(pain)))
        bounded_surprise = max(0.0, min(1.0, float(surprise)))

        if bounded_pain >= 0.85:
            return InvoluntaryExpression(
                kind="pain_vocalization",
                intentional=False,
                trigger="high_pain",
            )
        if bounded_surprise >= 0.95:
            return InvoluntaryExpression(
                kind="startle_vocalization",
                intentional=False,
                trigger="extreme_surprise",
            )
        return None
