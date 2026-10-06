from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json


@dataclass(frozen=True)
class SubjectiveFrameReceipt:
    canonical_source_seq: int
    canonical_tail_hash: str
    selector_version: str
    retrieval_policy_version: str
    renderer_id: str
    retrieved_source_event_ids: tuple[str, ...]
    recent_context_bounds: tuple[int, int]
    omitted_reasons: tuple[str, ...] = ()

    def digest(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(payload).hexdigest()
