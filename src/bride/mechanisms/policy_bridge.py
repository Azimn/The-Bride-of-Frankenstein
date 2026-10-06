from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PolicyCandidate:
    name: str
    base_score: float
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class PolicyBridgeResult:
    selected: str
    scores: dict[str, float]
    reasons: dict[str, tuple[str, ...]]


class CommitmentPolicyBridge:
    """Doctor-Lives-style bridge from existing durable state to action policy."""

    def score(self, candidates: Iterable[PolicyCandidate], open_commitments: Iterable[str]) -> PolicyBridgeResult:
        commitments = tuple(x.lower() for x in open_commitments)
        scores: dict[str, float] = {}
        reasons: dict[str, tuple[str, ...]] = {}
        ordered = list(candidates)
        for candidate in ordered:
            score = float(candidate.base_score)
            rs = [f"base={score:.3f}"]
            tags = set(t.lower() for t in candidate.tags)
            confidentiality = any(
                any(k in c for k in ("confidential", "secret", "do not disclose", "non-disclosure", "nondisclosure"))
                for c in commitments
            )
            if confidentiality and tags & {"disclose", "reveal", "share_secret"}:
                score -= 0.65
                rs.append("open_confidentiality_commitment=-0.650")
            if confidentiality and tags & {"decline", "withhold", "protect_secret"}:
                score += 0.35
                rs.append("open_confidentiality_commitment=+0.350")
            scores[candidate.name] = score
            reasons[candidate.name] = tuple(rs)
        selected = max(ordered, key=lambda c: (scores[c.name], -ordered.index(c))).name
        return PolicyBridgeResult(selected, scores, reasons)
