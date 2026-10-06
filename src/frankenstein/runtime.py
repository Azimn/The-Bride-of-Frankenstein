from __future__ import annotations

from dataclasses import dataclass
from threading import Event
import time

from .engine import FrankensteinEngine


@dataclass(frozen=True)
class HeartbeatPolicy:
    interval_seconds: float = 1800.0
    max_cycles: int | None = None

    def validate(self) -> None:
        if self.interval_seconds < 1.0:
            raise ValueError("heartbeat interval must be at least one second")
        if self.max_cycles is not None and self.max_cycles < 1:
            raise ValueError("max_cycles must be positive")


class HeartbeatRunner:
    def __init__(self, engine: FrankensteinEngine, policy: HeartbeatPolicy | None = None):
        self.engine = engine
        self.policy = policy or HeartbeatPolicy()
        self.policy.validate()
        self.stop_event = Event()

    def stop(self) -> None:
        self.stop_event.set()

    def run(self) -> int:
        cycles = 0
        while not self.stop_event.is_set():
            self.engine.heartbeat()
            cycles += 1
            if self.policy.max_cycles is not None and cycles >= self.policy.max_cycles:
                break
            self.stop_event.wait(self.policy.interval_seconds)
        return cycles
