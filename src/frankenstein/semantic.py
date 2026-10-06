from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
import json
import re
import urllib.request


@dataclass(frozen=True)
class ClaimProposal:
    subject: str
    predicate: str
    object: Any
    confidence: float = 0.5


@dataclass(frozen=True)
class InterpretationProposal:
    summary: str
    tags: tuple[str, ...] = ()
    relationship_deltas: dict[str, float] = field(default_factory=dict)
    claims: tuple[ClaimProposal, ...] = ()


class SemanticInterpreter(Protocol):
    interpreter_id: str
    def interpret(self, actor_id: str, text: str) -> InterpretationProposal: ...


class DeterministicInterpreter:
    interpreter_id = "deterministic-semantic-v1"

    def interpret(self, actor_id: str, text: str) -> InterpretationProposal:
        lower = text.lower()
        tags: list[str] = []
        deltas: dict[str, float] = {}
        if "?" in text:
            tags.append("question")
        if any(x in lower for x in ("thank you", "thanks", "appreciate")):
            tags.append("gratitude")
            deltas["trust"] = deltas.get("trust", 0.0) + 0.02
            deltas["attachment"] = deltas.get("attachment", 0.0) + 0.01
        if any(x in lower for x in ("i'm sorry", "i am sorry", "apologize")):
            tags.append("apology")
            deltas["resentment"] = deltas.get("resentment", 0.0) - 0.03
        if any(x in lower for x in ("i promise", "i will", "i'll")):
            tags.append("promise_language")
        if any(x in lower for x in ("hurt you", "kill you", "threat")):
            tags.append("threat")
            deltas["fear"] = deltas.get("fear", 0.0) + 0.08
            deltas["trust"] = deltas.get("trust", 0.0) - 0.05
        return InterpretationProposal(summary=f"{actor_id} communicated directly.", tags=tuple(tags), relationship_deltas=deltas)


@dataclass
class OllamaSemanticInterpreter:
    model: str
    base_url: str = "http://127.0.0.1:11434"
    timeout: float = 90.0
    interpreter_id: str = "ollama-semantic"

    def interpret(self, actor_id: str, text: str) -> InterpretationProposal:
        system = (
            "Return only JSON. You are a bounded semantic organ, not an authority. Analyze the social meaning of one observed utterance. "
            "Do not create commitments, goals, world facts, or memories. Relationship deltas must use only trust, familiarity, attachment, respect, obligation, resentment, fear and must each be between -0.12 and 0.12. "
            "Claims are hypotheses about the utterance content, not accepted beliefs."
        )
        schema = {
            "summary": "short subjective paraphrase",
            "tags": ["short_tag"],
            "relationship_deltas": {"trust": 0.0},
            "claims": [{"subject": actor_id, "predicate": "example", "object": "value", "confidence": 0.5}],
        }
        prompt = json.dumps({"speaker": actor_id, "utterance": text, "required_shape": schema}, ensure_ascii=False)
        body = json.dumps({"model": self.model, "stream": False, "format": "json", "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}).encode("utf-8")
        req = urllib.request.Request(self.base_url.rstrip("/") + "/api/chat", data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = str(data.get("message", {}).get("content", "{}"))
        parsed = json.loads(content)
        claims = tuple(ClaimProposal(str(c.get("subject", actor_id)), str(c.get("predicate", "")), c.get("object"), float(c.get("confidence", 0.5))) for c in parsed.get("claims", []) if c.get("predicate"))
        return InterpretationProposal(
            summary=str(parsed.get("summary", "")).strip(),
            tags=tuple(str(x) for x in parsed.get("tags", [])[:12]),
            relationship_deltas={str(k): float(v) for k, v in dict(parsed.get("relationship_deltas", {})).items()},
            claims=claims,
        )


@dataclass(frozen=True)
class InterpretationAdmission:
    summary: str
    tags: tuple[str, ...]
    relationship_deltas: dict[str, float]
    claims: tuple[ClaimProposal, ...]


class InterpretationPolicy:
    def __init__(self, relationship_dimensions: set[str], *, max_delta: float = 0.12, max_claims: int = 8):
        self.relationship_dimensions = set(relationship_dimensions)
        self.max_delta = abs(float(max_delta))
        self.max_claims = int(max_claims)

    def admit(self, proposal: InterpretationProposal) -> InterpretationAdmission:
        deltas: dict[str, float] = {}
        for key, value in proposal.relationship_deltas.items():
            if key not in self.relationship_dimensions:
                continue
            deltas[key] = max(-self.max_delta, min(self.max_delta, float(value)))
        tags = tuple(dict.fromkeys(re.sub(r"[^a-z0-9_:-]", "", t.lower().replace(" ", "_"))[:48] for t in proposal.tags if t.strip()))[:12]
        claims = tuple(c for c in proposal.claims if c.predicate.strip())[: self.max_claims]
        return InterpretationAdmission(proposal.summary.strip()[:1000], tags, deltas, claims)
