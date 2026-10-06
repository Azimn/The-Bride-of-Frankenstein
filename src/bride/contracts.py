from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


GOVERNING_QUESTION = (
    "Does changing this internal state predictably change what the same individual "
    "attends to, remembers, predicts, learns, decides, or does later, while preserving "
    "historical truth and architectural authority?"
)


class DonorRole(str, Enum):
    MECHANISM = "mechanism"
    EVALUATION = "evaluation"
    PROVENANCE = "provenance"
    HISTORICAL = "historical"
    DEPLOYMENT = "deployment"


class PromotionVerdict(str, Enum):
    PROMOTE = "promote"
    HOLD = "hold"
    REJECT = "reject"
    INFRASTRUCTURE_ONLY = "infrastructure_only"
    ADAPTER_ONLY = "adapter_only"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class MechanismSpec:
    mechanism_id: str
    donor: str
    title: str
    role: DonorRole
    hypothesis: str
    target_channels: tuple[str, ...]
    complexity_points: float = 1.0
    requires_model: bool = False
    notes: str = ""


@dataclass(frozen=True)
class SubjectSnapshot:
    identity_digest: str
    historical_truth_digest: str
    authority_digest: str
    replay_digest: str
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class ProbeResult:
    attended: tuple[str, ...] = ()
    remembered: tuple[str, ...] = ()
    predicted: tuple[str, ...] = ()
    learned: tuple[str, ...] = ()
    decided: str | None = None
    acted: str | None = None
    semantic_output: str | None = None
    latency_ms: float = 0.0
    state_size_bytes: int = 0
    notes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TrialObservation:
    baseline: ProbeResult
    challenger: ProbeResult
    baseline_snapshot: SubjectSnapshot
    challenger_snapshot: SubjectSnapshot
    intervention_label: str
    replicate: int


@dataclass(frozen=True)
class QualificationCase:
    case_id: str
    description: str
    intervention_label: str
    expected_channel: str
    expected_value: str | tuple[str, ...] | None = None
    minimum_effect: float = 0.25
    minimum_quality_gain: float = 0.25
    minimum_challenger_quality: float = 0.75
    minimum_replicates: int = 3
    require_renderer_invariance: bool = False
    maximum_latency_ratio: float = 2.0
    maximum_state_size_ratio: float = 2.0


@dataclass(frozen=True)
class QualificationResult:
    mechanism_id: str
    verdict: PromotionVerdict
    causal_effect: float
    consistency: float
    specificity: float
    baseline_quality: float
    challenger_quality: float
    quality_gain: float
    truth_preserved: bool
    authority_preserved: bool
    replay_preserved: bool
    identity_preserved: bool
    renderer_invariant: bool | None
    latency_ratio: float
    state_size_ratio: float
    passed_cases: tuple[str, ...]
    failed_cases: tuple[str, ...]
    reasons: tuple[str, ...]


class SubjectAdapter(Protocol):
    def fork(self) -> "SubjectAdapter": ...
    def snapshot(self) -> SubjectSnapshot: ...
    def apply_history(self, history: tuple[dict[str, Any], ...]) -> None: ...
    def intervene(self, mechanism_id: str, payload: dict[str, Any]) -> None: ...
    def probe(self, probe: dict[str, Any]) -> ProbeResult: ...


class Mechanism(Protocol):
    spec: MechanismSpec
    def intervention_payload(self, case: QualificationCase, replicate: int) -> dict[str, Any]: ...
