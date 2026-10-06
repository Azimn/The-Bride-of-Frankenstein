from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .storage import SQLiteStore


@dataclass(frozen=True)
class ActionCandidate:
    name: str
    base_utility: float = 0.0
    tags: tuple[str, ...] = ()
    relationship_weights: dict[str, float] = field(default_factory=dict)
    need_weights: dict[str, float] = field(default_factory=dict)
    affect_weights: dict[str, float] = field(default_factory=dict)
    goal_keywords: tuple[str, ...] = ()
    concern_keywords: tuple[str, ...] = ()
    required_capability: str | None = None


@dataclass(frozen=True)
class DecisionReceipt:
    selected: str
    scores: dict[str, float]
    reasons: dict[str, tuple[str, ...]]


class DecisionEngine:
    """The single action-selection authority for the character core."""

    def __init__(self, store: SQLiteStore, action_priors: dict[str, float] | None = None):
        self.store = store
        self.action_priors = action_priors or {}

    def decide(self, candidates: list[ActionCandidate], *, actor_id: str | None = None, context: str = "") -> DecisionReceipt:
        if not candidates:
            raise ValueError("at least one action candidate is required")
        with self.store.connect() as conn:
            needs = {r["name"]: float(r["value"]) for r in conn.execute("SELECT * FROM needs")}
            rel = {r["dimension"]: float(r["value"]) for r in conn.execute("SELECT * FROM relationships WHERE actor_id=?", (actor_id,))} if actor_id else {}
            affect = {r["axis"]: float(r["value"]) for r in conn.execute("SELECT * FROM affect")}
            habits = {r["action_name"]: float(r["value"]) for r in conn.execute("SELECT * FROM habits")}
            goals = [str(r["description"]).lower() for r in conn.execute("SELECT description FROM goals WHERE status='active'")]
            concerns = [str(r["description"]).lower() for r in conn.execute("SELECT description FROM concerns WHERE status='active'")]
            last = conn.execute("SELECT value_json FROM runtime_state WHERE key='last_action'").fetchone()
        last_name = ""
        if last:
            import json
            try:
                last_name = str(json.loads(last[0]).get("action_name", ""))
            except Exception:
                pass
        scores: dict[str, float] = {}
        reasons: dict[str, tuple[str, ...]] = {}
        context_l = context.lower()
        for c in candidates:
            score = float(c.base_utility) + float(self.action_priors.get(c.name, 0.0))
            rs: list[str] = [f"base={score:.3f}"]
            for dim, weight in c.relationship_weights.items():
                contribution = rel.get(dim, 0.0) * float(weight)
                score += contribution
                if abs(contribution) > 1e-9:
                    rs.append(f"relationship:{dim}={contribution:.3f}")
            for need, weight in c.need_weights.items():
                pressure = 1.0 - needs.get(need, 0.5)
                contribution = pressure * float(weight)
                score += contribution
                if abs(contribution) > 1e-9:
                    rs.append(f"need:{need}={contribution:.3f}")
            for axis, weight in c.affect_weights.items():
                contribution = affect.get(axis, 0.0) * float(weight)
                score += contribution
                if abs(contribution) > 1e-9:
                    rs.append(f"affect:{axis}={contribution:.3f}")
            if c.name in habits:
                contribution = habits[c.name] * 0.15
                score += contribution
                rs.append(f"habit={contribution:.3f}")
            if last_name == c.name:
                score += 0.04
                rs.append("inertia=0.040")
            for kw in c.goal_keywords:
                if kw.lower() in context_l or any(kw.lower() in g for g in goals):
                    score += 0.08
                    rs.append(f"goal:{kw}=0.080")
            for kw in c.concern_keywords:
                if kw.lower() in context_l or any(kw.lower() in x for x in concerns):
                    score += 0.08
                    rs.append(f"concern:{kw}=0.080")
            scores[c.name] = score
            reasons[c.name] = tuple(rs)
        selected = max(candidates, key=lambda c: (scores[c.name], -candidates.index(c))).name
        return DecisionReceipt(selected, scores, reasons)
