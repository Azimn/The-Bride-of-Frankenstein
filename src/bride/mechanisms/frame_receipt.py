from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Iterable


@dataclass(frozen=True)
class SubjectiveFrameReceipt:
    canonical_source_seq: int
    canonical_tail_hash: str
    selector_version: str
    retrieval_policy_version: str
    renderer_id: str
    retrieved_source_event_ids: tuple[str, ...]
    recent_context_bounds: tuple[int, int]
    retrieval_budget: int = 0
    actor_id: str | None = None
    omitted_reasons: tuple[str, ...] = ()

    def digest(self) -> str:
        payload = json.dumps(
            asdict(self),
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return hashlib.sha256(payload).hexdigest()


def build_subjective_frame_receipt(
    engine,
    *,
    actor_id: str | None,
    renderer_id: str,
    retrieved_hits: Iterable,
    retrieval_budget: int,
    selector_version: str = "frankenstein-decision-v1",
    retrieval_policy_version: str = "frankenstein-memory-v1",
    recent_dialogue_limit: int = 8,
    omitted_reasons: tuple[str, ...] = (),
) -> SubjectiveFrameReceipt:
    """Bind one renderer evidence surface to exact canonical provenance.

    The receipt is researcher-facing operational evidence. It is not placed in
    the character's SubjectiveFrame and therefore does not become first-person
    machine knowledge.
    """

    canonical = engine.store.iter_events(canonical_only=True)
    if canonical:
        source_seq = canonical[-1].seq
        tail_hash = canonical[-1].event_hash
    else:
        source_seq = 0
        tail_hash = "0" * 64

    context_events = []
    if actor_id is not None:
        context_events = [
            event
            for event in canonical
            if event.actor_id == actor_id
            and event.kind in {"social_observation", "subject_action"}
        ][-max(1, int(recent_dialogue_limit)):]

    if context_events:
        bounds = (context_events[0].seq, context_events[-1].seq)
    else:
        bounds = (0, 0)

    source_ids = tuple(
        str(hit.source_event_id)
        for hit in retrieved_hits
    )

    return SubjectiveFrameReceipt(
        canonical_source_seq=source_seq,
        canonical_tail_hash=tail_hash,
        selector_version=selector_version,
        retrieval_policy_version=retrieval_policy_version,
        renderer_id=str(renderer_id),
        retrieved_source_event_ids=source_ids,
        recent_context_bounds=bounds,
        retrieval_budget=max(0, int(retrieval_budget)),
        actor_id=actor_id,
        omitted_reasons=tuple(str(x) for x in omitted_reasons),
    )
