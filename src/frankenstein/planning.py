from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import json

from .decision import ActionCandidate
from .storage import SQLiteStore


@dataclass(frozen=True)
class PlanState:
    plan_id: str
    goal_id: str
    objective: str
    routes: tuple[tuple[str, ...], ...]
    route_index: int
    step_index: int
    status: str
    source_event_id: str

    @property
    def current_step(self) -> str | None:
        if self.status != "active":
            return None
        if not 0 <= self.route_index < len(self.routes):
            return None
        route = self.routes[self.route_index]
        if not 0 <= self.step_index < len(route):
            return None
        return route[self.step_index]

    @classmethod
    def from_payload(cls, payload: dict[str, Any], source_event_id: str) -> "PlanState":
        return cls(
            plan_id=str(payload["plan_id"]),
            goal_id=str(payload["goal_id"]),
            objective=str(payload["objective"]),
            routes=tuple(tuple(str(step) for step in route) for route in payload["routes"]),
            route_index=int(payload.get("route_index", 0)),
            step_index=int(payload.get("step_index", 0)),
            status=str(payload.get("status", "active")),
            source_event_id=source_event_id,
        )

    def payload(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal_id": self.goal_id,
            "objective": self.objective,
            "routes": [list(route) for route in self.routes],
            "route_index": self.route_index,
            "step_index": self.step_index,
            "status": self.status,
        }


class PlanProjection:
    """Read-only view of the replayable active-plan projection."""

    KEY = "active_plan"

    def __init__(self, store: SQLiteStore):
        self.store = store

    def current(self) -> PlanState | None:
        with self.store.connect() as conn:
            row = conn.execute(
                "SELECT value_json,source_event_id FROM runtime_state WHERE key=?",
                (self.KEY,),
            ).fetchone()
        if not row:
            return None
        payload = json.loads(row["value_json"])
        return PlanState.from_payload(payload, str(row["source_event_id"]))


def validate_routes(routes: tuple[tuple[str, ...], ...]) -> tuple[tuple[str, ...], ...]:
    normalized = tuple(
        tuple(str(step).strip() for step in route if str(step).strip())
        for route in routes
    )
    if not normalized or any(not route for route in normalized):
        raise ValueError("plans require at least one non-empty route")
    if len(normalized) > 8:
        raise ValueError("plans support at most eight alternate routes")
    if any(len(route) > 16 for route in normalized):
        raise ValueError("plan routes support at most sixteen steps")
    return normalized


def plan_action_candidate(
    state: PlanState | None,
    *,
    base_utility: float = 0.30,
) -> ActionCandidate | None:
    if state is None:
        return None
    step = state.current_step
    if step is None:
        return None
    return ActionCandidate(
        step,
        base_utility=float(base_utility),
        tags=("plan_step",),
        goal_keywords=(state.objective,),
    )
