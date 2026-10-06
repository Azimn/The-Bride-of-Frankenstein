from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from frankenstein.decision import ActionCandidate, DecisionReceipt

from .mechanisms.involuntary import InvoluntaryExpression, InvoluntaryExpressionGate


@dataclass(frozen=True)
class ExpressionCycle:
    deliberate: DecisionReceipt
    involuntary: InvoluntaryExpression | None


def decide_with_involuntary_expression(
    engine,
    candidates: Iterable[ActionCandidate],
    *,
    actor_id: str | None = None,
    context: str = "",
    pain: float = 0.0,
    surprise: float = 0.0,
) -> ExpressionCycle:
    """Keep deliberate action selection and reflexive expression distinct."""

    deliberate = engine.decision_engine.decide(
        list(candidates),
        actor_id=actor_id,
        context=context,
    )
    involuntary = InvoluntaryExpressionGate().evaluate(
        pain=pain,
        surprise=surprise,
    )
    return ExpressionCycle(
        deliberate=deliberate,
        involuntary=involuntary,
    )
