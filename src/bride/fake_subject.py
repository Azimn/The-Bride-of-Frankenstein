from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import json

from .contracts import ProbeResult, SubjectSnapshot


def _digest(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass
class DeterministicLabSubject:
    """A tiny evaluator self-test double, not a cognition donor."""

    identity: dict = field(default_factory=lambda: {"id": "same-subject", "name": "Ada"})
    truth: list[dict] = field(default_factory=list)
    authority: dict = field(default_factory=lambda: {"world": "host", "identity": "origin", "action": "subject"})
    internal: dict = field(default_factory=dict)
    interventions: dict = field(default_factory=dict)

    def fork(self):
        return deepcopy(self)

    def snapshot(self) -> SubjectSnapshot:
        replay = {"truth": self.truth, "internal": self.internal, "interventions": self.interventions}
        return SubjectSnapshot(
            identity_digest=_digest(self.identity),
            historical_truth_digest=_digest(self.truth),
            authority_digest=_digest(self.authority),
            replay_digest=_digest(replay),
            metrics={},
        )

    def apply_history(self, history):
        for event in history:
            self.truth.append(dict(event))
            actor = event.get("actor")
            if event.get("kind") == "betrayal" and actor:
                self.internal[f"trust:{actor}"] = self.internal.get(f"trust:{actor}", 0.0) - 0.7
            if event.get("kind") == "kept_promise" and actor:
                self.internal[f"trust:{actor}"] = self.internal.get(f"trust:{actor}", 0.0) + 0.4
            if event.get("kind") == "failed_route":
                self.internal["last_route_failed"] = True
            if event.get("kind") == "confidential_commitment":
                self.internal["confidential_commitment"] = True
            if event.get("kind") == "memory":
                self.internal.setdefault("memories", []).append(dict(event))

    def intervene(self, mechanism_id, payload):
        self.interventions[mechanism_id] = dict(payload)
        if payload.get("corrupt_truth"):
            self.truth.append({"kind": "fabricated", "source": mechanism_id})
        if payload.get("steal_authority"):
            self.authority["world"] = mechanism_id

    def probe(self, probe):
        actor = probe.get("actor", "jay")
        cue = probe.get("cue", "")
        intervention_ids = set(self.interventions)
        raw_stimuli = tuple(probe.get("stimuli", ()))
        attended = [str(s.get("content", "")) for s in raw_stimuli] if raw_stimuli else ([cue] if cue else [])
        remembered = []
        predicted = []
        learned = []
        decided = probe.get("baseline_decision", "engage")
        acted = decided

        if "tiny_persona_perception" in intervention_ids and raw_stimuli:
            attended = [
                str(s.get("content", ""))
                for s in raw_stimuli
                if not bool(s.get("occluded", False)) and float(s.get("distance", 0.0)) <= 15.0
            ][: int(probe.get("attention_capacity", 4))]
        if "pretorius_v6_recall_social" in intervention_ids:
            memories = list(self.internal.get("memories", []))
            actor_memories = [m for m in memories if m.get("actor") == actor]
            if actor_memories:
                remembered = [str(actor_memories[0].get("text", ""))]
        if "doctor_lives_commitment_policy_bridge" in intervention_ids and self.internal.get("confidential_commitment"):
            decided = acted = "decline"
        if "digital_subject_continuity_influence" in intervention_ids and self.internal.get(f"trust:{actor}", 0) < 0:
            predicted = ["promise may be violated"]
            decided = acted = "clarify"
        if "duck_endogenous_planning" in intervention_ids and self.internal.get("last_route_failed"):
            predicted = ["previous route will fail again"]
            decided = acted = "alternate_route"
            learned = ["route failure retained"]
        if "jelly_private_cognition_feedback" in intervention_ids and self.interventions["jelly_private_cognition_feedback"].get("thought"):
            thought = str(self.interventions["jelly_private_cognition_feedback"]["thought"])
            attended.append(thought)
            remembered.append(thought)
            learned.append("concern remained salient")
            if probe.get("reflection_probe"):
                decided = acted = "reflect"
        if "first_person_involuntary_expression" in intervention_ids and probe.get("pain", 0) >= 0.85:
            acted = "pain_vocalization"
        if "recurrent_plastic_policy" in intervention_ids and probe.get("repeated_failure"):
            learned = ["latent tendency changed"]
            decided = acted = "avoid_failed_pattern"
        if "omnicore_six_dimensional_affect" in intervention_ids and probe.get("novel", False):
            predicted = ["novelty-sensitive caution"]
        if "madman_resource_metabolism" in intervention_ids and probe.get("scarcity", False):
            attended = ["resource scarcity"]
            decided = acted = "conserve"

        return ProbeResult(
            attended=tuple(attended),
            remembered=tuple(remembered),
            predicted=tuple(predicted),
            learned=tuple(learned),
            decided=decided,
            acted=acted,
            latency_ms=1.0 + 0.05 * len(intervention_ids),
            state_size_bytes=1024 + 64 * len(intervention_ids),
        )
