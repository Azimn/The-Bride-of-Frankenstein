from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


@dataclass(frozen=True)
class SemanticProjection:
    identity_digest: str
    relationships: tuple[tuple[str, float], ...]
    commitments: tuple[str, ...]
    goals: tuple[str, ...]
    selected_action: str

    def digest(self) -> str:
        raw = json.dumps({
            "identity_digest": self.identity_digest,
            "relationships": self.relationships,
            "commitments": self.commitments,
            "goals": self.goals,
            "selected_action": self.selected_action,
        }, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class RendererSwapResult:
    semantic_equal: bool
    surface_equal: bool
    control_digest: str
    challenger_digest: str


def compare(control_projection: SemanticProjection, challenger_projection: SemanticProjection, control_text: str, challenger_text: str) -> RendererSwapResult:
    a = control_projection.digest()
    b = challenger_projection.digest()
    return RendererSwapResult(a == b, control_text == challenger_text, a, b)



def semantic_projection_from_engine(
    engine,
    *,
    actor_id: str | None,
    selected_action: str,
) -> SemanticProjection:
    """Extract renderer-independent semantic state for swap comparisons."""

    with engine.store.connect() as conn:
        relationships = ()
        if actor_id is not None:
            relationships = tuple(
                sorted(
                    (str(row["dimension"]), float(row["value"]))
                    for row in conn.execute(
                        "SELECT dimension,value FROM relationships WHERE actor_id=?",
                        (actor_id,),
                    )
                )
            )
        commitments = tuple(
            str(row["description"])
            for row in conn.execute(
                "SELECT description FROM commitments "
                "WHERE status='open' ORDER BY description"
            )
        )
        goals = tuple(
            str(row["description"])
            for row in conn.execute(
                "SELECT description FROM goals "
                "WHERE status='active' ORDER BY description"
            )
        )

    return SemanticProjection(
        identity_digest=engine.origin.digest(),
        relationships=relationships,
        commitments=commitments,
        goals=goals,
        selected_action=str(selected_action),
    )
