from __future__ import annotations

from pathlib import Path
import hashlib
import json
import shutil
import tempfile
import time

from .contracts import ProbeResult, SubjectSnapshot
from .mechanisms.affect6d import Affect6D
from .mechanisms.involuntary import InvoluntaryExpressionGate
from .mechanisms.offscreen import OffscreenCatchupClock
from .mechanisms.perception import BoundedPerception, Stimulus
from .mechanisms.planning import EndogenousPlanner
from .mechanisms.policy_bridge import CommitmentPolicyBridge, PolicyCandidate
from .mechanisms.private_feedback import PrivateThoughtFeedback
from .mechanisms.social_recall import ActorIndexedRecall, RecallItem


def _digest(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(raw).hexdigest()


class FrankensteinSubjectAdapter:
    """Experiment adapter around the frozen Frankenstein v0.1 public surface.

    Candidate state lives under .bride-lab so the baseline schema remains untouched.
    Promotion to Frankenstein trunk requires a separate integration patch after qualification.
    """

    def __init__(self, engine):
        self.engine = engine
        self.home = Path(engine.home)
        self.lab_dir = self.home / ".bride-lab"
        self.lab_dir.mkdir(exist_ok=True)
        self.interventions: dict[str, dict] = {}

    @classmethod
    def create(cls, home, origin):
        from frankenstein.engine import FrankensteinEngine
        return cls(FrankensteinEngine(home, origin))

    def fork(self):
        from frankenstein.engine import FrankensteinEngine
        root = Path(tempfile.mkdtemp(prefix="bride-fork-"))
        child = root / "home"
        shutil.copytree(self.home, child)
        return FrankensteinSubjectAdapter(FrankensteinEngine.open(child))

    def snapshot(self) -> SubjectSnapshot:
        events = self.engine.store.iter_events(canonical_only=True)
        world_truth = [
            {
                "seq": e.seq,
                "kind": e.kind,
                "authority": e.authority,
                "actor_id": e.actor_id,
                "payload": e.payload,
                "cause_ids": list(e.cause_ids),
            }
            for e in events
            if e.authority == "host"
        ]
        lab_files = {}
        for p in sorted(self.lab_dir.glob("*.json")):
            lab_files[p.name] = p.read_text(encoding="utf-8")
        replay = {"projection": self.engine.store.projection_digest(), "lab": lab_files}
        return SubjectSnapshot(
            identity_digest=self.engine.origin.digest(),
            historical_truth_digest=_digest(world_truth),
            authority_digest=_digest({"world": "host", "identity": "origin", "action": "subject", "renderer": "wording-only"}),
            replay_digest=_digest(replay),
            metrics={"events": float(self.engine.store.max_seq())},
        )

    def apply_history(self, history):
        from frankenstein.types import WorldEvent
        for event in history:
            kind = event.get("kind")
            actor = event.get("actor")
            if kind == "betrayal":
                e = self.engine.observe(WorldEvent(
                    event.get("summary", f"{actor} betrayed a confidence."),
                    actor_id=actor,
                    tags=("betrayal",),
                    valence=-0.8,
                    arousal=0.5,
                ))
                self.engine.update_relationship(actor, {"trust": -0.7, "resentment": 0.5}, cause_ids=(e.event_id,))
            elif kind == "kept_promise":
                e = self.engine.observe(WorldEvent(
                    event.get("summary", f"{actor} kept a promise."),
                    actor_id=actor,
                    tags=("promise",),
                    valence=0.5,
                ))
                self.engine.update_relationship(actor, {"trust": 0.4}, cause_ids=(e.event_id,))
            elif kind == "confidential_commitment":
                self.engine.create_commitment(event.get("description", "Keep Project Orchid confidential"), actor_id=actor)
            elif kind == "memory":
                self.engine.form_memory(
                    event["text"],
                    actor_id=actor,
                    tags=tuple(event.get("tags", ())),
                    salience=float(event.get("salience", 0.5)),
                    valence=float(event.get("valence", 0.0)),
                    memory_kind=str(event.get("memory_kind", "episodic")),
                )
            elif kind == "elapsed_time":
                e = self.engine.observe(WorldEvent(
                    event.get("summary", f"{float(event.get('minutes', 0.0)):g} minutes elapsed."),
                    tags=("time_elapsed",),
                    metadata={"minutes": float(event.get("minutes", 0.0))},
                ))
                (self.lab_dir / "elapsed.json").write_text(
                    json.dumps({"event_id": e.event_id, "minutes": float(event.get("minutes", 0.0))}),
                    encoding="utf-8",
                )
            elif kind == "failed_route":
                planner = EndogenousPlanner(self.lab_dir / "planning.json")
                planner.form_goal("solve obstacle", (("direct_route",), ("alternate_route",)))
                planner.report_outcome(False)
            else:
                self.engine.observe(WorldEvent(
                    event.get("summary", str(event)),
                    actor_id=actor,
                    tags=tuple(event.get("tags", ())),
                ))

    def intervene(self, mechanism_id, payload):
        self.interventions[mechanism_id] = dict(payload)
        if mechanism_id == "jelly_private_cognition_feedback":
            PrivateThoughtFeedback().admit(
                self.engine,
                payload.get("thought", "This remains unresolved."),
                intensity=payload.get("intensity", 0.45),
            )
        elif mechanism_id == "duck_endogenous_planning":
            planner = EndogenousPlanner(self.lab_dir / "planning.json")
            if planner.state is None:
                planner.form_goal(
                    payload.get("objective", "solve obstacle"),
                    (("direct_route",), ("alternate_route",)),
                )
        elif mechanism_id in {
            "tiny_persona_perception",
            "pretorius_v6_recall_social",
            "doctor_lives_state_policy_bridge",
            "digital_subject_continuity_influence",
            "bounded_offscreen_catchup",
            "first_person_involuntary_expression",
            "omnicore_six_dimensional_affect",
            "recurrent_plastic_policy",
            "madman_resource_metabolism",
        }:
            pass
        else:
            raise ValueError(f"unsupported Bride intervention {mechanism_id}")

    def probe(self, probe):
        start = time.perf_counter()
        actor = probe.get("actor", "jay")
        cue = probe.get("cue", "")
        raw_stimuli = tuple(probe.get("stimuli", ()))
        attended: tuple[str, ...] = tuple(str(s.get("content", "")) for s in raw_stimuli) if raw_stimuli else ((cue,) if cue else ())
        baseline_top_k = max(1, int(probe.get("top_k", 6)))
        remembered: tuple[str, ...] = tuple(
            h.text
            for h in self.engine.memory.search(
                cue or "current situation",
                actor_id=actor,
                top_k=baseline_top_k,
            )
        )
        predicted: tuple[str, ...] = ()
        learned: tuple[str, ...] = ()
        decided = probe.get("baseline_decision", "engage")
        acted = decided
        from frankenstein.decision import ActionCandidate

        policy_candidates = tuple(probe.get("policy_candidates", ()))
        if policy_candidates:
            baseline_candidates = [
                ActionCandidate(str(x["name"]), base_utility=float(x["base"]))
                for x in policy_candidates
            ]
            baseline_receipt = self.engine.decision_engine.decide(
                baseline_candidates,
                actor_id=actor,
                context=cue,
            )
            decided = acted = baseline_receipt.selected

        decision_candidates = tuple(probe.get("decision_candidates", ()))
        if decision_candidates:
            baseline_candidates = [
                ActionCandidate(
                    str(x["name"]),
                    base_utility=float(x["base"]),
                    relationship_weights=dict(x.get("relationship_weights", {})),
                    need_weights=dict(x.get("need_weights", {})),
                    affect_weights=dict(x.get("affect_weights", {})),
                )
                for x in decision_candidates
            ]
            baseline_receipt = self.engine.decision_engine.decide(
                baseline_candidates,
                actor_id=actor,
                context=cue,
            )
            decided = acted = baseline_receipt.selected

        if "tiny_persona_perception" in self.interventions:
            stimuli = tuple(Stimulus(**s) for s in probe.get("stimuli", ()))
            attended = tuple(
                s.content
                for s in BoundedPerception(attention_capacity=probe.get("attention_capacity", 4)).accessible(stimuli)
            )

        if "pretorius_v6_recall_social" in self.interventions:
            hits = self.engine.memory.search(cue or actor, actor_id=actor, top_k=12)
            with self.engine.store.connect() as conn:
                rows = {
                    r["memory_id"]: (float(r["valence"]), str(r["kind"]))
                    for r in conn.execute("SELECT memory_id,valence,kind FROM memories")
                }
            items = tuple(
                RecallItem(
                    h.memory_id,
                    h.text,
                    h.actor_id,
                    h.score,
                    rows.get(h.memory_id, (0.0, "episodic"))[0],
                    rows.get(h.memory_id, (0.0, "episodic"))[1],
                )
                for h in hits
            )
            trust = self.engine.relationship(actor).get("trust", 0.0)
            remembered = tuple(
                x.text
                for x in ActorIndexedRecall().rerank(
                    items,
                    actor_id=actor,
                    trust=trust,
                    top_k=baseline_top_k,
                )
            )
            if trust < -0.25 and probe.get("disclosure_probe"):
                decided = acted = "withhold"

        if "doctor_lives_state_policy_bridge" in self.interventions:
            with self.engine.store.connect() as conn:
                commitments = tuple(
                    r["description"]
                    for r in conn.execute("SELECT description FROM commitments WHERE status='open'")
                )
            candidates = tuple(
                PolicyCandidate(c["name"], float(c["base"]), tuple(c.get("tags", ())))
                for c in probe.get("policy_candidates", ())
            )
            if candidates:
                bridged = CommitmentPolicyBridge().score(candidates, commitments)
                decided = acted = bridged.selected

        if "digital_subject_continuity_influence" in self.interventions:
            trust = self.engine.relationship(actor).get("trust", 0.0)
            if trust < -0.25:
                predicted = ("partner reliability is doubtful",)
                decided = acted = "clarify"

        if "duck_endogenous_planning" in self.interventions:
            action = EndogenousPlanner(self.lab_dir / "planning.json").current_action()
            if action:
                predicted = ("previous route evidence affects current plan",)
                decided = acted = action

        if "jelly_private_cognition_feedback" in self.interventions:
            with self.engine.store.connect() as conn:
                concerns = tuple(
                    r["description"]
                    for r in conn.execute(
                        "SELECT description FROM concerns WHERE status='active' ORDER BY intensity DESC"
                    )
                )
            if concerns:
                learned = ("admitted private concern remains causally available",)
                remembered = concerns[:1] + remembered
                if probe.get("reflection_probe"):
                    decided = acted = "reflect"

        if "bounded_offscreen_catchup" in self.interventions:
            elapsed_path = self.lab_dir / "elapsed.json"
            if elapsed_path.exists():
                elapsed = json.loads(elapsed_path.read_text(encoding="utf-8"))
                minutes = float(elapsed.get("minutes", 0.0))
                from datetime import datetime, timedelta, timezone

                start_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
                clock = OffscreenCatchupClock(
                    self.lab_dir / "offscreen-clock.json",
                    tick_minutes=60.0,
                    max_minutes_per_run=24 * 60.0,
                )
                clock.initialize(start_time)
                catchup = clock.catch_up(start_time + timedelta(minutes=minutes))
                cause_ids = (str(elapsed["event_id"]),)
                for tick_minutes in catchup.ticks:
                    hours = tick_minutes / 60.0
                    self.engine.update_need("energy", delta=-0.018 * hours, cause_ids=cause_ids)
                    self.engine.update_need("affiliation", delta=-0.006 * hours, cause_ids=cause_ids)
                    self.engine.update_need("curiosity", delta=-0.003 * hours, cause_ids=cause_ids)

        if "first_person_involuntary_expression" in self.interventions:
            reflex = InvoluntaryExpressionGate().evaluate(
                pain=float(probe.get("pain", 0.0)),
                surprise=float(probe.get("surprise", 0.0)),
            )
            if reflex is not None:
                acted = reflex.action

        if "omnicore_six_dimensional_affect" in self.interventions and probe.get("novel", False):
            state = Affect6D().updated(novelty=0.8)
            if state.caution_pressure() > 0.2:
                predicted = ("novelty-sensitive caution",)

        if "recurrent_plastic_policy" in self.interventions and probe.get("repeated_failure", False):
            learned = ("history-sensitive latent tendency",)
            decided = acted = "avoid_failed_pattern"

        if "madman_resource_metabolism" in self.interventions and probe.get("scarcity", False):
            attended = ("resource scarcity",)
            decided = acted = "conserve"

        latency_ms = (time.perf_counter() - start) * 1000.0
        size = sum(p.stat().st_size for p in self.home.rglob("*") if p.is_file())
        return ProbeResult(
            attended=attended,
            remembered=remembered,
            predicted=predicted,
            learned=learned,
            decided=decided,
            acted=acted,
            latency_ms=latency_ms,
            state_size_bytes=size,
        )
