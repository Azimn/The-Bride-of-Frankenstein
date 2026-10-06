from __future__ import annotations

import pytest

from frankenstein.types import WorldEvent


def test_afterglow_does_not_delete_sources(engine):
    e = engine.observe(WorldEvent("A difficult conversation ends.", tags=("conversation",)))
    r = engine.lifecycle.afterglow((e.event_id,), "I am still thinking about how tense that felt.")
    assert engine.store.event(e.event_id) is not None
    assert e.event_id in r.cause_ids


def test_daily_consolidation_is_additive(engine):
    e = engine.observe(WorldEvent("A package arrives."))
    day = e.created_at[:10]
    summary = engine.lifecycle.consolidate_day(day, "A package arrived, which changed the day's plans.", (e.event_id,))
    assert engine.store.event(e.event_id) is not None
    assert summary.event_id != e.event_id
    hits = engine.memory.search("package arrived")
    assert len(hits) >= 2


def test_consolidation_requires_valid_day(engine):
    e = engine.observe(WorldEvent("Something happens."))
    with pytest.raises(ValueError, match="ISO"):
        engine.lifecycle.consolidate_day("yesterday", "summary", (e.event_id,))


def test_consolidation_requires_source(engine):
    with pytest.raises(ValueError, match="source"):
        engine.lifecycle.consolidate_day("2026-10-05", "summary", ())


def test_fractal_period_summaries_enter_coarse_context(engine):
    e = engine.observe(WorldEvent("The workshop opens for the season."))
    engine.lifecycle.consolidate_period("week", "2026-W40", "The workshop reopened and routines resumed.", (e.event_id,))
    engine.lifecycle.consolidate_period("month", "2026-10", "October began with the workshop reopening.", (e.event_id,))
    context = engine.lifecycle.long_horizon_context()
    assert "October began" in context[0]
    assert any("workshop reopened" in x for x in context)
    frame = engine.subjective_frame(actor_id=None, situation="Think about the workshop.", selected_move="reflect")
    assert frame.long_horizon_context == context
