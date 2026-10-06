from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable

from .storage import SQLiteStore
from .types import Authority, EventKind, EventRecord, new_id


class LifecycleManager:
    def __init__(self, store: SQLiteStore, append_canonical):
        self.store = store
        self.append_canonical = append_canonical

    def afterglow(self, source_event_ids: Iterable[str], text: str, *, tags: tuple[str, ...] = ()) -> EventRecord:
        source = tuple(source_event_ids)
        if not source:
            raise ValueError("afterglow requires source events")
        return self.append_canonical(EventKind.REFLECTION_NOTE, Authority.SUBJECT, {
            "memory_id": new_id(),
            "text": text,
            "memory_kind": "reflection",
            "salience": 0.55,
            "valence": 0.0,
            "arousal": 0.0,
            "tags": list(tags),
        }, cause_ids=source)

    def consolidate_day(self, day: str, summary: str, source_event_ids: Iterable[str]) -> EventRecord:
        try:
            datetime.fromisoformat(day)
        except ValueError as exc:
            raise ValueError("day must be ISO formatted YYYY-MM-DD") from exc
        source = tuple(source_event_ids)
        if not source:
            raise ValueError("consolidation requires source events")
        return self.append_canonical(EventKind.CONSOLIDATION_SUMMARY, Authority.SUBJECT, {
            "memory_id": new_id(),
            "text": summary,
            "memory_kind": "daily_summary",
            "salience": 0.45,
            "valence": 0.0,
            "arousal": 0.0,
            "tags": ["consolidated", day],
            "period": day,
        }, cause_ids=source)


    def consolidate_period(self, period_kind: str, period_key: str, summary: str, source_event_ids: Iterable[str]) -> EventRecord:
        allowed = {"day", "week", "month", "quarter", "year", "life"}
        if period_kind not in allowed:
            raise ValueError("period_kind must be one of: " + ", ".join(sorted(allowed)))
        source = tuple(source_event_ids)
        if not source:
            raise ValueError("consolidation requires source events")
        return self.append_canonical(EventKind.CONSOLIDATION_SUMMARY, Authority.SUBJECT, {
            "memory_id": new_id(),
            "text": summary,
            "memory_kind": f"{period_kind}_summary",
            "salience": 0.40,
            "valence": 0.0,
            "arousal": 0.0,
            "tags": ["consolidated", period_kind, period_key],
            "period_kind": period_kind,
            "period": period_key,
        }, cause_ids=source)

    def long_horizon_context(self, *, per_tier: int = 1) -> tuple[str, ...]:
        tiers = ("life_summary", "year_summary", "quarter_summary", "month_summary", "week_summary", "day_summary")
        out: list[str] = []
        with self.store.connect() as conn:
            for tier in tiers:
                rows = conn.execute("SELECT text FROM memories WHERE kind=? ORDER BY created_at DESC LIMIT ?", (tier, per_tier)).fetchall()
                out.extend(str(r["text"]) for r in reversed(rows))
        return tuple(out)

    def event_ids_for_day(self, day: str) -> list[str]:
        return [e.event_id for e in self.store.iter_events(canonical_only=True) if e.created_at.startswith(day)]
