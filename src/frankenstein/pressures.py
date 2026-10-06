from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .decision import ActionCandidate
from .private_cognition import active_private_concerns
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
    """Apply narrow confidentiality pressure without selecting an action.

    A confidentiality commitment becomes relevant only when disclosure is
    genuinely among the available actions. This prevents unrelated decisions
    from acquiring a generic refusal bias merely because a secret exists.
    """

    ordered = tuple(candidates)
    labels_by_name = {
        candidate.name: _semantic_labels(candidate)
        for candidate in ordered
    }
    commitments_l = tuple(str(text).lower() for text in commitments)
    confidentiality = any(
        any(marker in commitment for marker in _CONFIDENTIALITY_MARKERS)
        for commitment in commitments_l
    )
    disclosure_in_choice = any(
        labels & _DISCLOSURE_ACTIONS
        for labels in labels_by_name.values()
    )
    active = confidentiality and disclosure_in_choice

    out: list[ActionCandidate] = []
    for candidate in ordered:
        delta = 0.0
        labels = labels_by_name[candidate.name]
        if active and labels & _DISCLOSURE_ACTIONS:
            delta -= 0.65
        if active and labels & _PROTECTION_ACTIONS:
            delta += 0.35
        out.append(
            replace(
                candidate,
                base_utility=float(candidate.base_utility) + delta,
            )
        )
    return tuple(out)


_REFLECTION_ACTIONS = {"reflect", "review_concern", "consider"}


def private_concern_adjusted_candidates(
    candidates: Iterable[ActionCandidate],
    store: SQLiteStore,
) -> tuple[ActionCandidate, ...]:
    """Apply bounded private-concern pressure without selecting an action."""

    ordered = tuple(candidates)
    concerns = active_private_concerns(store)
    max_intensity = max(
        (intensity for _, intensity in concerns),
        default=0.0,
    )

    out: list[ActionCandidate] = []
    for candidate in ordered:
        labels = _semantic_labels(candidate)
        delta = max_intensity if labels & _REFLECTION_ACTIONS else 0.0
        out.append(
            replace(
                candidate,
                base_utility=float(candidate.base_utility) + delta,
            )
        )
    return tuple(out)
