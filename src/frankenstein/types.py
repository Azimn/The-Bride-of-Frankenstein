from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import json
import re
import uuid


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Authority(str, Enum):
    HOST = "host"
    SUBJECT = "subject"
    RENDERER = "renderer"
    SYSTEM = "system"
    EXTERNAL = "external"


class Canonicality(str, Enum):
    CANONICAL = "canonical"
    NONCANONICAL = "noncanonical"


class EventKind(str, Enum):
    WORLD_EVENT = "world_event"
    SOCIAL_OBSERVATION = "social_observation"
    SUBJECT_ACTION = "subject_action"
    ACTION_OUTCOME = "action_outcome"
    RELATIONSHIP_UPDATE = "relationship_update"
    NEED_UPDATE = "need_update"
    BELIEF_UPDATE = "belief_update"
    COMMITMENT_CREATED = "commitment_created"
    COMMITMENT_UPDATED = "commitment_updated"
    GOAL_CREATED = "goal_created"
    GOAL_UPDATED = "goal_updated"
    CONCERN_UPDATE = "concern_update"
    MEMORY_FORMED = "memory_formed"
    REFLECTION_NOTE = "reflection_note"
    CONSOLIDATION_SUMMARY = "consolidation_summary"
    RENDERER_OUTPUT = "renderer_output"
    PRIVATE_THOUGHT_PROPOSAL = "private_thought_proposal"
    DECISION_RECEIPT = "decision_receipt"
    CHECKPOINT = "checkpoint"
    INTERPRETATION_PROPOSAL = "interpretation_proposal"
    INTERPRETATION = "interpretation"
    AFFECT_UPDATE = "affect_update"
    EXPECTATION_CREATED = "expectation_created"
    EXPECTATION_UPDATED = "expectation_updated"


@dataclass(frozen=True)
class EventRecord:
    seq: int
    event_id: str
    created_at: str
    kind: str
    authority: str
    canonicality: str
    actor_id: str | None
    payload: dict[str, Any]
    cause_ids: tuple[str, ...]
    prev_hash: str
    event_hash: str


@dataclass(frozen=True)
class WorldEvent:
    summary: str
    actor_id: str | None = None
    tags: tuple[str, ...] = ()
    salience: float = 0.5
    valence: float = 0.0
    arousal: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.summary.strip():
            raise ValueError("world event summary cannot be empty")
        for name, value in (("salience", self.salience), ("valence", self.valence), ("arousal", self.arousal)):
            if not -1.0 <= value <= 1.0 and name != "salience":
                raise ValueError(f"{name} must be between -1 and 1")
        if not 0.0 <= self.salience <= 1.0:
            raise ValueError("salience must be between 0 and 1")


@dataclass(frozen=True)
class SubjectiveFrame:
    situation: str
    relationship: str
    bodily_state: tuple[str, ...]
    affective_state: tuple[str, ...]
    active_commitments: tuple[str, ...]
    active_goals: tuple[str, ...]
    recalled_memories: tuple[str, ...]
    recent_dialogue: tuple[str, ...]
    long_horizon_context: tuple[str, ...]
    concerns: tuple[str, ...]
    selected_move: str
    voice_constraints: tuple[str, ...]

    def as_prompt_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RenderedResponse:
    text: str
    renderer_id: str
    raw: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.text.strip():
            raise ValueError("renderer returned empty text")


@dataclass(frozen=True)
class IntegrityReport:
    ok: bool
    checked_events: int
    errors: tuple[str, ...] = ()


_UUID_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.I)


def new_id() -> str:
    return str(uuid.uuid4())


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def looks_like_uuid(text: str) -> bool:
    return bool(_UUID_RE.search(text))
