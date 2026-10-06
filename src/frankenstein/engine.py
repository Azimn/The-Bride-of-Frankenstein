from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
import json

from .capabilities import CapabilityGate
from .cartridge import CharacterOrigin
from .decision import ActionCandidate, DecisionEngine, DecisionReceipt
from .firewall import assert_subjective_safe, qualitative_affect, qualitative_need, qualitative_relationship
from .lifecycle import LifecycleManager
from .lock import FileLock
from .semantic import InterpretationPolicy, SemanticInterpreter
from .memory import MemoryIndex
from .projections import ProjectionManager
from .renderer import DeterministicRenderer, Renderer
from .storage import SQLiteStore
from .types import Authority, Canonicality, EventKind, EventRecord, SubjectiveFrame, WorldEvent, new_id


_SOCIAL_MOVES = [
    ActionCandidate("engage", base_utility=0.25, relationship_weights={"trust": 0.35, "attachment": 0.15}, need_weights={"affiliation": 0.20}),
    ActionCandidate("clarify", base_utility=0.20, relationship_weights={"trust": -0.05}, concern_keywords=("uncertain", "conflict")),
    ActionCandidate("repair", base_utility=0.05, relationship_weights={"resentment": 0.30, "attachment": 0.20}, concern_keywords=("repair", "betrayal", "conflict")),
    ActionCandidate("withdraw", base_utility=0.0, relationship_weights={"fear": 0.55, "trust": -0.45}, need_weights={"safety": 0.35}, affect_weights={"tension": 0.25}),
]


class FrankensteinEngine:
    def __init__(self, home: str | Path, origin: CharacterOrigin, *, renderer: Renderer | None = None, capabilities: CapabilityGate | None = None, interpreter: SemanticInterpreter | None = None):
        self.home = Path(home)
        self.home.mkdir(parents=True, exist_ok=True)
        self.origin = origin
        self.writer_lock = FileLock(self.home / ".writer.lock")
        origin.validate()
        self.origin_path = self.home / "character.origin.json"
        self.db_path = self.home / "state.sqlite3"
        if self.origin_path.exists():
            existing = CharacterOrigin.load(self.origin_path)
            if existing.digest() != origin.digest():
                raise ValueError("sealed character origin differs from the existing home")
        else:
            origin.save(self.origin_path)
        self.store = SQLiteStore(self.db_path)
        self.store.set_meta("origin_digest", origin.digest())
        self.projections = ProjectionManager(self.store, origin)
        with self.writer_lock:
            self.projections.ensure_current()
        self.memory = MemoryIndex(self.store)
        self.decision_engine = DecisionEngine(self.store, origin.action_priors)
        self.renderer = renderer or DeterministicRenderer()
        self.capabilities = capabilities or CapabilityGate()
        self.interpreter = interpreter
        self.interpretation_policy = InterpretationPolicy(set(origin.relationship_defaults))
        self.lifecycle = LifecycleManager(self.store, self._append_canonical)

    @classmethod
    def open(cls, home: str | Path, *, renderer: Renderer | None = None, capabilities: CapabilityGate | None = None, interpreter: SemanticInterpreter | None = None) -> "FrankensteinEngine":
        home = Path(home)
        return cls(home, CharacterOrigin.load(home / "character.origin.json"), renderer=renderer, capabilities=capabilities, interpreter=interpreter)

    def _append(self, kind, authority, payload, *, actor_id=None, cause_ids=(), canonicality=Canonicality.CANONICAL) -> EventRecord:
        with self.writer_lock:
            self.projections.ensure_current()
            event = self.store.append_event(kind, authority, payload, actor_id=actor_id, cause_ids=tuple(cause_ids), canonicality=canonicality)
            self.projections.apply_event(event)
            return event

    def _append_canonical(self, kind, authority, payload, *, actor_id=None, cause_ids=()) -> EventRecord:
        return self._append(kind, authority, payload, actor_id=actor_id, cause_ids=cause_ids, canonicality=Canonicality.CANONICAL)

    def observe(self, event: WorldEvent) -> EventRecord:
        event.validate()
        e = self._append_canonical(EventKind.WORLD_EVENT, Authority.HOST, {
            "summary": event.summary,
            "tags": list(event.tags),
            "salience": event.salience,
            "valence": event.valence,
            "arousal": event.arousal,
            "metadata": event.metadata,
        }, actor_id=event.actor_id)
        self.form_memory(event.summary, actor_id=event.actor_id, tags=event.tags, salience=event.salience, valence=event.valence, arousal=event.arousal, cause_ids=(e.event_id,))
        if abs(event.valence) > 1e-9 or abs(event.arousal) > 1e-9:
            self.update_affect({
                "valence": event.valence * 0.25,
                "arousal": event.arousal * 0.25,
                "tension": max(0.0, -event.valence) * 0.15 + abs(event.arousal) * 0.10,
            }, cause_ids=(e.event_id,))
        return e

    def social_observation(self, actor_id: str, text: str, *, tags: tuple[str, ...] = ()) -> EventRecord:
        if not text.strip():
            raise ValueError("social observation text cannot be empty")
        e = self._append_canonical(EventKind.SOCIAL_OBSERVATION, Authority.HOST, {"text": text, "tags": list(tags)}, actor_id=actor_id)
        self.form_memory(f'{actor_id} said: "{text}"', actor_id=actor_id, tags=("speech",) + tuple(tags), salience=0.45, cause_ids=(e.event_id,))
        if self.interpreter is not None:
            self.interpret_social_observation(e.event_id)
        return e

    def interpret_social_observation(self, event_id: str) -> EventRecord:
        if self.interpreter is None:
            raise RuntimeError("no semantic interpreter is configured")
        observed = self.store.event(event_id)
        if not observed or observed.kind != EventKind.SOCIAL_OBSERVATION.value:
            raise ValueError("semantic interpretation requires a social observation event")
        actor_id = observed.actor_id or "unknown"
        proposal = self.interpreter.interpret(actor_id, str(observed.payload.get("text", "")))
        proposal_event = self._append(EventKind.INTERPRETATION_PROPOSAL, Authority.EXTERNAL, {
            "interpreter_id": getattr(self.interpreter, "interpreter_id", "unknown"),
            "summary": proposal.summary,
            "tags": list(proposal.tags),
            "relationship_deltas": proposal.relationship_deltas,
            "claims": [{"subject": c.subject, "predicate": c.predicate, "object": c.object, "confidence": c.confidence} for c in proposal.claims],
        }, actor_id=actor_id, cause_ids=(event_id,), canonicality=Canonicality.NONCANONICAL)
        admitted = self.interpretation_policy.admit(proposal)
        interpretation = self._append_canonical(EventKind.INTERPRETATION, Authority.SUBJECT, {
            "summary": admitted.summary, "tags": list(admitted.tags),
            "relationship_deltas": admitted.relationship_deltas,
            "claim_count": len(admitted.claims),
            "proposal_event_id": proposal_event.event_id,
        }, actor_id=actor_id, cause_ids=(event_id, proposal_event.event_id))
        if admitted.relationship_deltas:
            self.update_relationship(actor_id, admitted.relationship_deltas, cause_ids=(interpretation.event_id,))
        if admitted.summary:
            self.form_memory(admitted.summary, actor_id=actor_id, tags=("interpretation",) + admitted.tags, salience=0.35, memory_kind="interpretation", cause_ids=(interpretation.event_id,))
        return interpretation

    def form_memory(self, text: str, *, actor_id: str | None = None, tags: tuple[str, ...] = (), salience: float = 0.5, valence: float = 0.0, arousal: float = 0.0, memory_kind: str = "episodic", cause_ids: tuple[str, ...] = ()) -> EventRecord:
        return self._append_canonical(EventKind.MEMORY_FORMED, Authority.SUBJECT, {
            "memory_id": new_id(), "memory_kind": memory_kind, "actor_id": actor_id, "text": text, "tags": list(tags),
            "salience": salience, "valence": valence, "arousal": arousal,
        }, actor_id=actor_id, cause_ids=cause_ids)

    def update_relationship(self, actor_id: str, deltas: dict[str, float], *, cause_ids: tuple[str, ...] = ()) -> EventRecord:
        unknown = set(deltas) - set(self.origin.relationship_defaults)
        if unknown:
            raise ValueError("unknown relationship dimensions: " + ", ".join(sorted(unknown)))
        return self._append_canonical(EventKind.RELATIONSHIP_UPDATE, Authority.SUBJECT, {"actor_id": actor_id, "deltas": deltas}, actor_id=actor_id, cause_ids=cause_ids)

    def update_need(self, name: str, *, delta: float | None = None, value: float | None = None, cause_ids: tuple[str, ...] = ()) -> EventRecord:
        if (delta is None) == (value is None):
            raise ValueError("provide exactly one of delta or value")
        payload: dict[str, Any] = {"name": name}
        payload["delta" if delta is not None else "value"] = delta if delta is not None else value
        return self._append_canonical(EventKind.NEED_UPDATE, Authority.SYSTEM, payload, cause_ids=cause_ids)

    def update_affect(self, deltas: dict[str, float], *, cause_ids: tuple[str, ...] = ()) -> EventRecord:
        allowed = {"valence", "arousal", "tension"}
        unknown = set(deltas) - allowed
        if unknown:
            raise ValueError("unknown affect axes: " + ", ".join(sorted(unknown)))
        bounded = {k: max(-0.5, min(0.5, float(v))) for k, v in deltas.items()}
        return self._append_canonical(EventKind.AFFECT_UPDATE, Authority.SYSTEM, {"deltas": bounded}, cause_ids=cause_ids)

    def set_belief(self, subject: str, predicate: str, obj: Any, *, confidence: float, evidence: tuple[str, ...], belief_id: str | None = None) -> EventRecord:
        if not evidence:
            raise ValueError("belief updates require evidence event ids")
        return self._append_canonical(EventKind.BELIEF_UPDATE, Authority.SUBJECT, {
            "belief_id": belief_id or new_id(), "subject": subject, "predicate": predicate, "object": obj,
            "confidence": confidence, "evidence": list(evidence), "status": "active",
        }, cause_ids=evidence)

    def create_commitment(self, description: str, *, actor_id: str | None = None, due_at: str | None = None, cause_ids: tuple[str, ...] = ()) -> str:
        cid = new_id()
        self._append_canonical(EventKind.COMMITMENT_CREATED, Authority.SUBJECT, {"commitment_id": cid, "description": description, "actor_id": actor_id, "due_at": due_at}, actor_id=actor_id, cause_ids=cause_ids)
        return cid

    def update_commitment(self, commitment_id: str, status: str, *, cause_ids: tuple[str, ...] = ()) -> EventRecord:
        if status not in {"open", "fulfilled", "broken", "cancelled"}:
            raise ValueError("invalid commitment status")
        return self._append_canonical(EventKind.COMMITMENT_UPDATED, Authority.SUBJECT, {"commitment_id": commitment_id, "status": status}, cause_ids=cause_ids)

    def create_expectation(self, description: str, *, actor_id: str | None = None, confidence: float = 0.5, due_at: str | None = None, cause_ids: tuple[str, ...] = ()) -> str:
        eid = new_id()
        self._append_canonical(EventKind.EXPECTATION_CREATED, Authority.SUBJECT, {"expectation_id": eid, "description": description, "actor_id": actor_id, "confidence": confidence, "due_at": due_at}, actor_id=actor_id, cause_ids=cause_ids)
        return eid

    def update_expectation(self, expectation_id: str, status: str, *, cause_ids: tuple[str, ...] = ()) -> EventRecord:
        if status not in {"open", "confirmed", "violated", "cancelled"}:
            raise ValueError("invalid expectation status")
        with self.store.connect() as conn:
            row = conn.execute("SELECT actor_id FROM expectations WHERE expectation_id=?", (expectation_id,)).fetchone()
        if not row:
            raise ValueError("unknown expectation")
        actor_id = row["actor_id"]
        event = self._append_canonical(EventKind.EXPECTATION_UPDATED, Authority.SUBJECT, {"expectation_id": expectation_id, "status": status}, actor_id=actor_id, cause_ids=cause_ids)
        if actor_id and status == "confirmed":
            self.update_relationship(actor_id, {"trust": 0.04}, cause_ids=(event.event_id,))
        elif actor_id and status == "violated":
            self.update_relationship(actor_id, {"trust": -0.10, "resentment": 0.08}, cause_ids=(event.event_id,))
            self.update_affect({"valence": -0.08, "tension": 0.10}, cause_ids=(event.event_id,))
        return event

    def create_goal(self, description: str, *, priority: float = 0.5, parent_goal_id: str | None = None, cause_ids: tuple[str, ...] = ()) -> str:
        gid = new_id()
        self._append_canonical(EventKind.GOAL_CREATED, Authority.SUBJECT, {"goal_id": gid, "description": description, "priority": priority, "parent_goal_id": parent_goal_id}, cause_ids=cause_ids)
        return gid

    def update_goal(self, goal_id: str, status: str, *, cause_ids: tuple[str, ...] = ()) -> EventRecord:
        if status not in {"active", "completed", "abandoned", "blocked"}:
            raise ValueError("invalid goal status")
        return self._append_canonical(EventKind.GOAL_UPDATED, Authority.SUBJECT, {"goal_id": goal_id, "status": status}, cause_ids=cause_ids)

    def set_concern(self, description: str, *, intensity: float = 0.5, concern_id: str | None = None, status: str = "active", cause_ids: tuple[str, ...] = ()) -> str:
        cid = concern_id or new_id()
        self._append_canonical(EventKind.CONCERN_UPDATE, Authority.SUBJECT, {"concern_id": cid, "description": description, "intensity": intensity, "status": status}, cause_ids=cause_ids)
        return cid

    def decide(self, candidates: list[ActionCandidate], *, actor_id: str | None = None, context: str = "") -> DecisionReceipt:
        receipt = self.decision_engine.decide(candidates, actor_id=actor_id, context=context)
        self._append_canonical(EventKind.DECISION_RECEIPT, Authority.SYSTEM, {"selected": receipt.selected, "scores": receipt.scores, "reasons": {k: list(v) for k, v in receipt.reasons.items()}}, actor_id=actor_id)
        return receipt

    def record_outcome(self, action_name: str, *, reward: float, summary: str, cause_ids: tuple[str, ...] = ()) -> EventRecord:
        return self._append_canonical(EventKind.ACTION_OUTCOME, Authority.HOST, {"action_name": action_name, "reward": reward, "summary": summary}, cause_ids=cause_ids)

    def private_thought(self, text: str, *, source_event_ids: tuple[str, ...] = ()) -> EventRecord:
        return self._append(EventKind.PRIVATE_THOUGHT_PROPOSAL, Authority.RENDERER, {"text": text}, cause_ids=source_event_ids, canonicality=Canonicality.NONCANONICAL)

    def admit_reflection(self, proposal_event_id: str, text: str) -> EventRecord:
        proposal = self.store.event(proposal_event_id)
        if not proposal or proposal.kind != EventKind.PRIVATE_THOUGHT_PROPOSAL.value:
            raise ValueError("reflection admission requires a private-thought proposal")
        return self.lifecycle.afterglow((proposal_event_id,), text, tags=("reflection",))


    def recent_dialogue(self, actor_id: str, *, limit: int = 8) -> tuple[str, ...]:
        events = [e for e in self.store.iter_events(canonical_only=True) if e.actor_id == actor_id and e.kind in {EventKind.SOCIAL_OBSERVATION.value, EventKind.SUBJECT_ACTION.value}]
        lines: list[str] = []
        for e in events[-max(1, limit):]:
            if e.kind == EventKind.SOCIAL_OBSERVATION.value:
                lines.append(f"{actor_id}: {e.payload.get('text', '')}")
            else:
                lines.append(f"{self.origin.display_name}: {e.payload.get('speech', '')}")
        return tuple(lines)

    def advance_time(self, minutes: float) -> EventRecord:
        if minutes <= 0 or minutes > 60 * 24 * 7:
            raise ValueError("minutes must be greater than zero and no more than seven days per advance")
        tick = self._append_canonical(EventKind.WORLD_EVENT, Authority.HOST, {"summary": f"{minutes:g} minutes elapsed.", "tags": ["time_elapsed"], "minutes": float(minutes)})
        hours = minutes / 60.0
        updates = {
            "energy": -0.018 * hours,
            "affiliation": -0.006 * hours,
            "curiosity": -0.003 * hours,
        }
        for name, delta in updates.items():
            self.update_need(name, delta=delta, cause_ids=(tick.event_id,))
        with self.store.connect() as conn:
            affect = {r["axis"]: float(r["value"]) for r in conn.execute("SELECT * FROM affect")}
        decay = {}
        for axis, value in affect.items():
            if abs(value) > 1e-9:
                decay[axis] = -value * min(0.5, 0.06 * hours)
        if decay:
            self.update_affect(decay, cause_ids=(tick.event_id,))
        return tick

    def heartbeat(self) -> DecisionReceipt:
        candidates = [
            ActionCandidate("rest", base_utility=0.08, need_weights={"energy": 0.85}),
            ActionCandidate("review_commitments", base_utility=0.12, goal_keywords=("commit",)),
            ActionCandidate("pursue_goal", base_utility=0.10, goal_keywords=("finish", "complete", "build", "write")),
            ActionCandidate("reflect", base_utility=0.09, concern_keywords=("conflict", "uncertain", "repair")),
        ]
        receipt = self.decide(candidates, context="autonomous heartbeat")
        self._append_canonical(EventKind.SUBJECT_ACTION, Authority.SUBJECT, {"action_name": receipt.selected, "speech": "", "autonomous": True})
        return receipt

    def relationship(self, actor_id: str) -> dict[str, float]:
        with self.store.connect() as conn:
            rows = conn.execute("SELECT dimension,value FROM relationships WHERE actor_id=?", (actor_id,)).fetchall()
        result = dict(self.origin.relationship_defaults)
        result.update({r["dimension"]: float(r["value"]) for r in rows})
        return result

    def subjective_frame(self, *, actor_id: str | None, situation: str, selected_move: str, memory_query: str | None = None) -> SubjectiveFrame:
        with self.store.connect() as conn:
            needs = {r["name"]: float(r["value"]) for r in conn.execute("SELECT * FROM needs")}
            affect = {r["axis"]: float(r["value"]) for r in conn.execute("SELECT * FROM affect")}
            commitments = tuple(r["description"] for r in conn.execute("SELECT description FROM commitments WHERE status='open' ORDER BY rowid DESC LIMIT 5"))
            goals = tuple(r["description"] for r in conn.execute("SELECT description FROM goals WHERE status='active' ORDER BY priority DESC LIMIT 5"))
            concerns = tuple(r["description"] for r in conn.execute("SELECT description FROM concerns WHERE status='active' ORDER BY intensity DESC LIMIT 5"))
        bodily = tuple(x for x in (qualitative_need(name, value) for name, value in needs.items()) if x)
        hits = self.memory.search(memory_query or situation, actor_id=actor_id, top_k=6)
        recent_dialogue = self.recent_dialogue(actor_id, limit=8) if actor_id else ()
        frame = SubjectiveFrame(
            situation=situation,
            relationship=qualitative_relationship(self.relationship(actor_id)) if actor_id else "No specific relationship is foregrounded.",
            bodily_state=bodily,
            affective_state=qualitative_affect(affect),
            active_commitments=commitments,
            active_goals=goals,
            recalled_memories=tuple(h.text for h in hits),
            recent_dialogue=recent_dialogue,
            long_horizon_context=self.lifecycle.long_horizon_context(),
            concerns=concerns,
            selected_move=selected_move,
            voice_constraints=tuple(self.origin.voice),
        )
        assert_subjective_safe(frame)
        return frame

    def chat(self, actor_id: str, user_text: str) -> str:
        obs = self.social_observation(actor_id, user_text)
        receipt = self.decision_engine.decide(_SOCIAL_MOVES, actor_id=actor_id, context=user_text)
        self._append_canonical(EventKind.DECISION_RECEIPT, Authority.SYSTEM, {"selected": receipt.selected, "scores": receipt.scores, "reasons": {k: list(v) for k, v in receipt.reasons.items()}}, actor_id=actor_id, cause_ids=(obs.event_id,))
        frame = self.subjective_frame(actor_id=actor_id, situation=f"{actor_id} is speaking with you now.", selected_move=receipt.selected, memory_query=user_text)
        rendered = self.renderer.render(frame, user_text=user_text)
        rendered.validate()
        render_event = self._append(EventKind.RENDERER_OUTPUT, Authority.RENDERER, {"text": rendered.text, "renderer_id": rendered.renderer_id, "raw": rendered.raw}, actor_id=actor_id, cause_ids=(obs.event_id,), canonicality=Canonicality.NONCANONICAL)
        self._append_canonical(EventKind.SUBJECT_ACTION, Authority.SUBJECT, {"action_name": receipt.selected, "speech": rendered.text, "renderer_event_id": render_event.event_id}, actor_id=actor_id, cause_ids=(obs.event_id, render_event.event_id))
        return rendered.text

    def execute_action(self, candidate: ActionCandidate, payload: dict[str, Any]) -> Any:
        decision = self.capabilities.authorize(candidate.required_capability)
        if not decision.allowed:
            raise PermissionError(decision.reason)
        if candidate.required_capability:
            return self.capabilities.execute(candidate.required_capability, payload)
        return payload

    def status(self) -> dict[str, Any]:
        self.projections.ensure_current()
        with self.store.connect() as conn:
            counts = {
                "events": conn.execute("SELECT COUNT(*) FROM events").fetchone()[0],
                "memories": conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0],
                "relationships": conn.execute("SELECT COUNT(DISTINCT actor_id) FROM relationships").fetchone()[0],
                "open_commitments": conn.execute("SELECT COUNT(*) FROM commitments WHERE status='open'").fetchone()[0],
                "open_expectations": conn.execute("SELECT COUNT(*) FROM expectations WHERE status='open'").fetchone()[0],
                "active_goals": conn.execute("SELECT COUNT(*) FROM goals WHERE status='active'").fetchone()[0],
            }
        integrity = self.store.verify_integrity()
        return {
            "entity_id": self.origin.entity_id,
            "display_name": self.origin.display_name,
            "origin_digest": self.origin.digest(),
            "projection_digest": self.store.projection_digest(),
            "projection_cursor": self.store.projection_cursor(),
            "max_event_seq": self.store.max_seq(),
            "integrity_ok": integrity.ok,
            **counts,
        }

    def rebuild(self) -> str:
        with self.writer_lock:
            self.projections.rebuild()
            return self.store.projection_digest()
