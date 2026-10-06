from __future__ import annotations

import json
import shutil

import pytest

from frankenstein.cartridge import CharacterOrigin
from frankenstein.decision import ActionCandidate
from frankenstein.engine import FrankensteinEngine
from frankenstein.types import Authority, Canonicality, EventKind, WorldEvent


def test_origin_is_sealed(tmp_path, origin):
    home = tmp_path / "home"
    FrankensteinEngine(home, origin)
    changed = CharacterOrigin(entity_id=origin.entity_id, display_name="Different")
    with pytest.raises(ValueError, match="sealed character origin"):
        FrankensteinEngine(home, changed)


def test_world_event_forms_memory(engine):
    e = engine.observe(WorldEvent("A bell rings in the hall.", tags=("bell", "hall"), salience=0.8))
    assert e.kind == EventKind.WORLD_EVENT.value
    hits = engine.memory.search("bell hall")
    assert hits and "bell" in hits[0].text.lower()


def test_external_speech_is_event_not_truth(engine):
    engine.social_observation("alex", "The moon is made of glass.")
    with engine.store.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM beliefs").fetchone()[0] == 0


def test_belief_requires_evidence(engine):
    with pytest.raises(ValueError, match="require evidence"):
        engine.set_belief("alex", "reliable", True, confidence=0.5, evidence=())
    obs = engine.social_observation("alex", "I arrived on time.")
    engine.set_belief("alex", "arrived_on_time", True, confidence=0.6, evidence=(obs.event_id,))
    with engine.store.connect() as conn:
        row = conn.execute("SELECT evidence_json FROM beliefs").fetchone()
    assert obs.event_id in json.loads(row[0])


def test_renderer_cannot_write_canonical_belief(engine):
    with pytest.raises(ValueError):
        engine.store.append_event(EventKind.BELIEF_UPDATE, Authority.RENDERER, {"bad": True})


def test_private_thought_is_noncanonical(engine):
    p = engine.private_thought("Perhaps I should leave.")
    assert p.canonicality == Canonicality.NONCANONICAL.value
    with engine.store.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0] == 0


def test_admitted_reflection_preserves_proposal_lineage(engine):
    p = engine.private_thought("Perhaps I should leave.")
    r = engine.admit_reflection(p.event_id, "I considered leaving, but I am not committed to it.")
    assert p.event_id in r.cause_ids
    assert engine.memory.search("considered leaving")


def test_relationship_is_multidimensional(engine):
    engine.update_relationship("alex", {"trust": 0.5, "resentment": 0.3})
    rel = engine.relationship("alex")
    assert rel["trust"] == pytest.approx(0.5)
    assert rel["resentment"] == pytest.approx(0.3)
    assert "attachment" in rel


def test_unknown_relationship_dimension_fails(engine):
    with pytest.raises(ValueError, match="unknown relationship"):
        engine.update_relationship("alex", {"telepathy": 1.0})


def test_commitment_and_goal_survive_restart(engine):
    engine.create_commitment("Return the book", actor_id="alex")
    engine.create_goal("Finish the inventory", priority=0.9)
    reopened = FrankensteinEngine.open(engine.home)
    status = reopened.status()
    assert status["open_commitments"] == 1
    assert status["active_goals"] == 1


def test_path_dependence_changes_choice(tmp_path, origin):
    base = FrankensteinEngine(tmp_path / "base", origin)
    base.social_observation("alex", "Can I help?")
    shutil.copytree(base.home, tmp_path / "trusted")
    shutil.copytree(base.home, tmp_path / "betrayed")
    trusted = FrankensteinEngine.open(tmp_path / "trusted")
    betrayed = FrankensteinEngine.open(tmp_path / "betrayed")
    trusted.update_relationship("alex", {"trust": 0.8})
    betrayed.update_relationship("alex", {"trust": -0.8, "fear": 0.6})
    choices = [
        ActionCandidate("accept", 0.1, relationship_weights={"trust": 0.8}),
        ActionCandidate("avoid", 0.1, relationship_weights={"trust": -0.6, "fear": 0.7}),
    ]
    assert trusted.decide(choices, actor_id="alex").selected == "accept"
    assert betrayed.decide(choices, actor_id="alex").selected == "avoid"


def test_reinforcement_changes_future_policy(engine):
    before = engine.decide([ActionCandidate("engage", 0.1), ActionCandidate("withdraw", 0.1)])
    engine.record_outcome("withdraw", reward=1.0, summary="Withdrawal prevented harm.")
    after = engine.decide([ActionCandidate("engage", 0.1), ActionCandidate("withdraw", 0.1)])
    assert after.scores["withdraw"] > before.scores["withdraw"]


def test_replay_reconstructs_causal_state(engine):
    w = engine.observe(WorldEvent("A green light appears.", tags=("green", "light")))
    engine.update_relationship("alex", {"trust": 0.4}, cause_ids=(w.event_id,))
    engine.create_commitment("Check the light", actor_id="alex", cause_ids=(w.event_id,))
    engine.create_goal("Understand the signal", priority=0.7, cause_ids=(w.event_id,))
    engine.record_outcome("engage", reward=0.7, summary="The signal was harmless.", cause_ids=(w.event_id,))
    before = engine.store.projection_digest()
    engine.projections.rebuild()
    assert engine.store.projection_digest() == before


def test_recent_dialogue_is_bounded(engine):
    for i in range(12):
        engine.chat("alex", f"message {i}")
    lines = engine.recent_dialogue("alex", limit=6)
    assert len(lines) == 6
    assert "message 11" in lines[-2]


def test_advance_time_changes_needs_through_host_event(engine):
    before = engine.status()["events"]
    tick = engine.advance_time(120)
    assert tick.kind == EventKind.WORLD_EVENT.value
    with engine.store.connect() as conn:
        energy = conn.execute("SELECT value FROM needs WHERE name='energy'").fetchone()[0]
    assert energy < engine.origin.baseline_needs["energy"]
    assert engine.status()["events"] > before


def test_advance_time_is_bounded(engine):
    with pytest.raises(ValueError):
        engine.advance_time(0)
    with pytest.raises(ValueError):
        engine.advance_time(60 * 24 * 8)


def test_unknown_schema_version_fails_closed(tmp_path):
    import sqlite3
    from frankenstein.storage import SQLiteStore
    path = tmp_path / "future.sqlite3"
    store = SQLiteStore(path)
    with store.transaction() as conn:
        conn.execute("UPDATE meta SET value='999' WHERE key='schema_version'")
    with pytest.raises(RuntimeError, match="unsupported database schema"):
        SQLiteStore(path)
