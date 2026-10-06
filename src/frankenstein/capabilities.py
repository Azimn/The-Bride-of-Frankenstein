from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any


@dataclass(frozen=True)
class CapabilityDecision:
    allowed: bool
    capability: str
    reason: str


class CapabilityGate:
    def __init__(self, allowed: set[str] | None = None):
        self.allowed = set(allowed or ())
        self.handlers: dict[str, Callable[[dict[str, Any]], Any]] = {}

    def register(self, capability: str, handler: Callable[[dict[str, Any]], Any], *, enabled: bool = False) -> None:
        self.handlers[capability] = handler
        if enabled:
            self.allowed.add(capability)

    def authorize(self, capability: str | None) -> CapabilityDecision:
        if not capability:
            return CapabilityDecision(True, "internal", "no external capability required")
        if capability not in self.handlers:
            return CapabilityDecision(False, capability, "capability is not registered by the host")
        if capability not in self.allowed:
            return CapabilityDecision(False, capability, "capability is registered but not enabled")
        return CapabilityDecision(True, capability, "host capability is enabled")

    def execute(self, capability: str, payload: dict[str, Any]) -> Any:
        decision = self.authorize(capability)
        if not decision.allowed:
            raise PermissionError(decision.reason)
        return self.handlers[capability](payload)
