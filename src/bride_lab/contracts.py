from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Verdict(str, Enum):
    PROMOTE = "promote"
    PROMOTE_INFRASTRUCTURE = "promote_infrastructure"
    QUALIFY_ADAPTER = "qualify_adapter"
    HOLD = "hold"
    BLOCKED = "blocked"
    REJECT = "reject"


@dataclass(frozen=True)
class Metric:
    name: str
    baseline: float
    candidate: float
    minimum_delta: float = 0.10
    higher_is_better: bool = True

    @property
    def delta(self) -> float:
        raw = self.candidate - self.baseline
        return raw if self.higher_is_better else -raw

    @property
    def improved(self) -> bool:
        return self.delta >= self.minimum_delta


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass(frozen=True)
class QualificationResult:
    mechanism_id: str
    donor: tuple[str, ...]
    verdict: Verdict
    metrics: tuple[Metric, ...] = ()
    gates: tuple[GateResult, ...] = ()
    complexity_cost: float = 0.0
    evidence_tier: str = "A-deterministic"
    rationale: str = ""
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def all_required_gates_pass(self) -> bool:
        return all(g.passed for g in self.gates)

    @property
    def has_behavior_gain(self) -> bool:
        return any(m.improved for m in self.metrics)

    @property
    def automatically_promotable(self) -> bool:
        return self.all_required_gates_pass and self.has_behavior_gain and self.complexity_cost <= 0.35
