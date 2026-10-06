from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecallItem:
    memory_id: str
    text: str
    actor_id: str | None
    score: float
    valence: float = 0.0
    memory_kind: str = "episodic"


class ActorIndexedRecall:
    """Pretorius V6-inspired social recall with explicit provenance preference."""

    def rerank(
        self,
        items: tuple[RecallItem, ...],
        *,
        actor_id: str | None,
        trust: float,
        top_k: int = 6,
    ) -> tuple[RecallItem, ...]:
        scored: list[tuple[float, RecallItem]] = []
        for item in items:
            score = float(item.score)

            if item.memory_kind == "episodic":
                score += 0.10
            elif item.memory_kind in {"interpretation", "reflection", "consolidation_summary"}:
                score -= 0.20

            if actor_id and item.actor_id == actor_id:
                score += 0.20
                if trust < -0.25 and item.valence < 0:
                    score += min(0.35, abs(trust) * abs(item.valence) * 0.5)

            scored.append((score, item))

        scored.sort(key=lambda x: (-x[0], x[1].memory_id))
        return tuple(item for _, item in scored[:top_k])
