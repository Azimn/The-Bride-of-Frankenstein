from __future__ import annotations

from dataclasses import dataclass

from frankenstein.engine import FrankensteinEngine
from frankenstein.semantic import ClaimProposal, DeterministicInterpreter, InterpretationProposal
from frankenstein.types import Canonicality, EventKind


@dataclass
class MaliciousInterpreter:
    interpreter_id: str = "malicious-test"
    def interpret(self, actor_id: str, text: str):
        return InterpretationProposal(
            summary="I interpret this as extremely important.",
            tags=("Important Social Event", "../../bad"),
            relationship_deltas={"trust": 99.0, "fear": -99.0, "telepathy": 1.0},
            claims=(ClaimProposal(actor_id, "owns_moon", True, 1.0),),
        )


def test_deterministic_interpreter_is_bounded(tmp_path, origin):
    engine = FrankensteinEngine(tmp_path / "home", origin, interpreter=DeterministicInterpreter())
    obs = engine.social_observation("alex", "Thank you. I promise I will come back.")
    rel = engine.relationship("alex")
    assert 0 < rel["trust"] <= 0.12
    events = engine.store.iter_events()
    proposal = [e for e in events if e.kind == EventKind.INTERPRETATION_PROPOSAL.value][-1]
    admitted = [e for e in events if e.kind == EventKind.INTERPRETATION.value][-1]
    assert proposal.canonicality == Canonicality.NONCANONICAL.value
    assert admitted.canonicality == Canonicality.CANONICAL.value
    assert obs.event_id in proposal.cause_ids
    assert proposal.event_id in admitted.cause_ids


def test_malicious_interpreter_cannot_escape_policy(tmp_path, origin):
    engine = FrankensteinEngine(tmp_path / "home", origin, interpreter=MaliciousInterpreter())
    engine.social_observation("alex", "hello")
    rel = engine.relationship("alex")
    assert rel["trust"] == 0.12
    assert rel["fear"] == -0.12
    assert "telepathy" not in rel
    with engine.store.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM beliefs").fetchone()[0] == 0
        memory = conn.execute("SELECT kind,tags_json FROM memories WHERE kind='interpretation'").fetchone()
    assert memory is not None
    assert "../" not in memory["tags_json"]
