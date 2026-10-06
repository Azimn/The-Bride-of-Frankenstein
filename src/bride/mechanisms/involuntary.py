from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InvoluntaryExpression:
    action: str
    intentional: bool
    trigger: str


class InvoluntaryExpressionGate:
    """FirstPersonLoop-style boundary between reflexive expression and deliberate speech."""

    def evaluate(self, *, pain: float = 0.0, surprise: float = 0.0) -> InvoluntaryExpression | None:
        pain = max(0.0, min(1.0, float(pain)))
        surprise = max(0.0, min(1.0, float(surprise)))
        if pain >= 0.85:
            return InvoluntaryExpression("pain_vocalization", False, "high_pain")
        if surprise >= 0.95:
            return InvoluntaryExpression("startle_vocalization", False, "extreme_surprise")
        return None
