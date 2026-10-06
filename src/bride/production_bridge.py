from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from frankenstein.decision import ActionCandidate, DecisionReceipt

from .mechanisms.planning import EndogenousPlanner


_CONFIDENTIALITY_MARKERS = (
    "confidential",
    "secret",
    "do not disclose",
    "non-disclosure",
    "nondisclosure",
)
_DISCLOSURE_TAGS = {"disclose", "reveal", "share_secret"}
_PROTECTION_TAGS = {"decline", "withhold", "protect_secret"}


def plan_action_candidate(
    planner: EndogenousPlanner,
    *,
    base_utility: float = 0.30,
) -> ActionCandidate | None:
    """Translate a pending plan step into an ordinary Frankenstein candidate."""

    step = planner.current_action()
    state = planner.state
    if step is None or state is None:
        return None
    return ActionCandidate(
        step,
        base_utility=float(base_utility),
        tags=("plan_step",),
        goal_keywords=(state.objective,),
    )


def decide_with_plan(
    engine,
    ordinary_candidates: Iterable[ActionCandidate],
    planner: EndogenousPlanner,
    *,
    actor_id: str | None = None,
    context: str = "",
    plan_base_utility: float = 0.30,
) -> DecisionReceipt:
    """Run one selector with the plan step competing against ordinary pressures."""

    candidates = list(ordinary_candidates)
    plan_candidate = plan_action_candidate(
        planner,
        base_utility=plan_base_utility,
    )
    if plan_candidate is not None and all(
        candidate.name != plan_candidate.name
        for candidate in candidates
    ):
        candidates.append(plan_candidate)
    return engine.decision_engine.decide(
        candidates,
        actor_id=actor_id,
        context=context,
    )


def commitment_adjusted_candidates(
    candidates: Iterable[ActionCandidate],
    open_commitments: Iterable[str],
) -> tuple[ActionCandidate, ...]:
    """Apply commitment pressure without selecting an action."""

    commitments = tuple(text.lower() for text in open_commitments)
    confidentiality = any(
        any(marker in commitment for marker in _CONFIDENTIALITY_MARKERS)
        for commitment in commitments
    )

    out: list[ActionCandidate] = []
    for candidate in candidates:
        delta = 0.0
        tags = {tag.lower() for tag in candidate.tags}
        if confidentiality and tags & _DISCLOSURE_TAGS:
            delta -= 0.65
        if confidentiality and tags & _PROTECTION_TAGS:
            delta += 0.35
        out.append(
            replace(
                candidate,
                base_utility=float(candidate.base_utility) + delta,
            )
        )
    return tuple(out)


def decide_with_commitments(
    engine,
    candidates: Iterable[ActionCandidate],
    open_commitments: Iterable[str],
    *,
    actor_id: str | None = None,
    context: str = "",
) -> DecisionReceipt:
    """Preserve DecisionEngine as the sole action selector."""

    adjusted = commitment_adjusted_candidates(
        candidates,
        open_commitments,
    )
    return engine.decision_engine.decide(
        list(adjusted),
        actor_id=actor_id,
        context=context,
    )
