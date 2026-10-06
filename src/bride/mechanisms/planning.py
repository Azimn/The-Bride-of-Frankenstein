from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json


@dataclass
class PlanState:
    objective: str
    routes: tuple[tuple[str, ...], ...]
    route_index: int = 0
    step_index: int = 0
    status: str = "active"

    @property
    def current_step(self) -> str | None:
        if self.status != "active" or self.route_index >= len(self.routes):
            return None
        route = self.routes[self.route_index]
        if self.step_index >= len(route):
            return None
        return route[self.step_index]


class EndogenousPlanner:
    """DUCK-inspired bounded planning sidecar used only inside Bride experiments."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.state: PlanState | None = self._load()

    def _load(self) -> PlanState | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        data["routes"] = tuple(tuple(r) for r in data["routes"])
        return PlanState(**data)

    def _save(self) -> None:
        if self.state is None:
            if self.path.exists():
                self.path.unlink()
            return
        self.path.write_text(json.dumps(asdict(self.state), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def form_goal(self, objective: str, routes: tuple[tuple[str, ...], ...]) -> bool:
        if self.state is not None and self.state.status == "active":
            return False
        if not objective.strip() or len(routes) < 2 or any(not route for route in routes):
            return False
        self.state = PlanState(objective=objective, routes=routes)
        self._save()
        return True

    def current_action(self) -> str | None:
        return self.state.current_step if self.state else None

    def report_outcome(self, success: bool) -> str | None:
        if self.state is None or self.state.status != "active":
            return None
        if success:
            self.state.step_index += 1
            route = self.state.routes[self.state.route_index]
            if self.state.step_index >= len(route):
                self.state.status = "completed"
        else:
            self.state.route_index += 1
            self.state.step_index = 0
            if self.state.route_index >= len(self.state.routes):
                self.state.status = "abandoned"
        self._save()
        return self.current_action()
