from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json


@dataclass(frozen=True)
class CatchupResult:
    elapsed_minutes: float
    applied_minutes: float
    deferred_minutes: float
    ticks: tuple[float, ...]


class OffscreenCatchupClock:
    """Host-owned bounded wall-clock catch-up."""

    def __init__(self, path: str | Path, *, tick_minutes: float = 30.0, max_minutes_per_run: float = 24 * 60.0):
        if tick_minutes <= 0 or max_minutes_per_run <= 0:
            raise ValueError("tick and cap must be positive")
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.tick_minutes = float(tick_minutes)
        self.max_minutes_per_run = float(max_minutes_per_run)

    def _state(self) -> dict:
        if not self.path.exists():
            return {"last_seen": None, "deferred_minutes": 0.0}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, state: dict) -> None:
        self.path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def initialize(self, now: datetime) -> None:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        self._save({"last_seen": now.astimezone(timezone.utc).isoformat(), "deferred_minutes": 0.0})

    def catch_up(self, now: datetime) -> CatchupResult:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        state = self._state()
        if state["last_seen"] is None:
            self.initialize(now)
            return CatchupResult(0.0, 0.0, 0.0, ())
        last = datetime.fromisoformat(state["last_seen"])
        elapsed = max(0.0, (now.astimezone(timezone.utc) - last).total_seconds() / 60.0)
        total = elapsed + float(state.get("deferred_minutes", 0.0))
        applied = min(total, self.max_minutes_per_run)
        deferred = max(0.0, total - applied)
        ticks: list[float] = []
        remaining = applied
        while remaining > 1e-9:
            step = min(self.tick_minutes, remaining)
            ticks.append(step)
            remaining -= step
        self._save({"last_seen": now.astimezone(timezone.utc).isoformat(), "deferred_minutes": deferred})
        return CatchupResult(elapsed, applied, deferred, tuple(ticks))
