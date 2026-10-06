from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .decision import ActionCandidate
from .storage import SQLiteStore


_CONFIDENTIALITY_MARKERS = (
    "confidential",
    "secret",
    "do not disclose",
    "non-disclosure",
    "nondisclosure",
)
_DISCLOSURE_ACTIONS = {"disclose", "reveal", "share_secret"}
_PROTECTION_ACTIONS = {"decline", "withhold", "protect_secret"}


def open_commitments(store: SQLiteStore) -> tuple[str, ...]:
    with store.connect() as conn:
        rows = conn.execute(
            "SELECT description FROM commitments "
            "WHERE status='open' ORDER BY rowid"
        ).fetchall()
    return tuple(str(row["description"]) for row in rows)


def _semantic_labels(candidate: ActionCandidate) -> set[str]:
    labels = {candidate.name.lower()}
    labels.update(tag.lower() for tag in candidate.tags)
    return labels


def commitment_adjusted_candidates(
    candidates: Iterable[ActionCandidate],
    commitments: Iterable[str],
) -> tuple[ActionCandidate, ...]:
    """Apply narrow confidentiality pressure without selecting an action."""

    commitments_l = tuple(str(text).lower() for text in commitments)
    confidentiality = any(
        any(marker in commitment for marker in _CONFIDENTIALITY_MARKERS)
        for commitment in commitments_l
    )

    out: list[ActionCandidate] = []
    for candidate in candidates:
        delta = 0.0
        labels = _semantic_labels(candidate)
        if confidentiality and labels & _DISCLOSURE_ACTIONS:
            delta -= 0.65
        if confidentiality and labels & _PROTECTION_ACTIONS:
            delta += 0.35
        out.append(
            replace(
                candidate,
                base_utility=float(candidate.base_utility) + delta,
            )
        )
    return tuple(out)
