from __future__ import annotations

import re

from .storage import SQLiteStore


PRIVATE_CONCERN_PREFIX = "Private concern, not established fact:"

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


def validate_private_thought(text: str) -> str:
    """Validate renderer-originated thought before any event is stored."""

    clean = _WS.sub(" ", str(text).strip())
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


def private_concern_text(clean_thought: str) -> str:
    return f"{PRIVATE_CONCERN_PREFIX} {clean_thought}"


def existing_private_concern(
    store: SQLiteStore,
    concern_text: str,
) -> str | None:
    with store.connect() as conn:
        row = conn.execute(
            "SELECT concern_id FROM concerns "
            "WHERE status='active' AND description=? LIMIT 1",
            (concern_text,),
        ).fetchone()
    return str(row["concern_id"]) if row else None


def active_private_concerns(
    store: SQLiteStore,
) -> tuple[tuple[str, float], ...]:
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT description,intensity FROM concerns "
            "WHERE status='active' AND description LIKE ? "
            "ORDER BY intensity DESC, concern_id",
            (PRIVATE_CONCERN_PREFIX + "%",),
        ).fetchall()
    return tuple(
        (
            str(row["description"]),
            max(0.0, min(0.65, float(row["intensity"]))),
        )
        for row in rows
    )
