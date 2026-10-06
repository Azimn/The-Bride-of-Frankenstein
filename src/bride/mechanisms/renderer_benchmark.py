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
