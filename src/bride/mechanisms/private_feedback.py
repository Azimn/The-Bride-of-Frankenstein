from __future__ import annotations

import re


_FORBIDDEN_MARKERS = (
    "source_event_id",
    "event_hash",
    "prev_hash",
    "projection_cursor",
    "raw_score",
    "utility_score",
    "checkpoint_sha",
    "memory_id",
    "concern_id",
    "goal_id",
    "commitment_id",
    "trust=",
    "valence=",
    "arousal=",
    "tension=",
)

_UUID = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.I,
)
_WS = re.compile(r"\s+")


class PrivateThoughtFeedback:
    """Jelly-Psiduck-inspired bounded admission path.

    Raw renderer thought never becomes canonical autobiography. The only admitted
    effect is an explicitly uncertain concern. Duplicate concerns do not stack.
    """

    @staticmethod
    def _normalize(text: str) -> str:
        return _WS.sub(" ", text.strip())

    @classmethod
    def _validate(cls, text: str) -> str:
        clean = cls._normalize(text)
        if not clean:
            raise ValueError("private thought cannot be empty")
        lowered = clean.lower()
        for marker in _FORBIDDEN_MARKERS:
            if marker in lowered:
                raise ValueError(f"private thought leaked machine marker {marker}")
        if _UUID.search(clean):
            raise ValueError("private thought leaked machine identifier")
        if len(clean) > 240:
            clean = clean[:237].rstrip() + "..."
        return clean

    def admit(self, engine, text: str, *, intensity: float = 0.45):
        clean = self._validate(text)
        concern_text = f"Private concern, not established fact: {clean}"

        with engine.store.connect() as conn:
            existing = conn.execute(
                "SELECT concern_id FROM concerns "
                "WHERE status='active' AND description=? LIMIT 1",
                (concern_text,),
            ).fetchone()
        if existing:
            proposal = engine.private_thought(clean)
            return proposal.event_id, None, str(existing["concern_id"])

        proposal = engine.private_thought(clean)
        concern_id = engine.set_concern(
            concern_text,
            intensity=max(0.0, min(0.65, float(intensity))),
            cause_ids=(proposal.event_id,),
        )
        return proposal.event_id, None, concern_id
