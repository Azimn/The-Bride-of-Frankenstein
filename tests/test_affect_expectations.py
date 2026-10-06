from __future__ import annotations

import pytest

from frankenstein.decision import ActionCandidate
from frankenstein.types import WorldEvent


def test_world_appraisal_creates_affective_residue(engine):
    engine.observe(WorldEvent("A sudden crash comes from the dark hall.", valence=-0.8, arousal=0.9))
    with engine.store.connect() as conn:
        affect = {r["axis"]: r["value"] for r in conn.execute("SELECT * FROM affect")}
    assert affect["valence"] < 0
    assert affect["arousal"] > 0
    assert affect["tension"] > 0
    frame = engine.subjective_frame(actor_id=None, situation="The hall is quiet again.", selected_move="reflect")
    assert any("Tension" in x for x in frame.affective_state)


def test_affect_can_change_action_selection(engine):
    calm = engine.decide([ActionCandidate("approach", 0.2), ActionCandidate("wait", 0.1, affect_weights={"tension": 0.8})])
    engine.update_affect({"tension": 0.8})
    tense = engine.decide([ActionCandidate("approach", 0.2), ActionCandidate("wait", 0.1, affect_weights={"tension": 0.8})])
    assert calm.selected == "approach"
    assert tense.selected == "wait"


def test_time_decays_affective_residue(engine):
    engine.update_affect({"tension": 0.5})
    with engine.store.connect() as conn:
        before = conn.execute("SELECT value FROM affect WHERE axis='tension'").fetchone()[0]
    engine.advance_time(180)
    with engine.store.connect() as conn:
        after = conn.execute("SELECT value FROM affect WHERE axis='tension'").fetchone()[0]
    assert 0 <= after < before


def test_expectation_confirmation_and_violation_have_different_social_effects(tmp_path, origin):
    from frankenstein.engine import FrankensteinEngine
    import shutil
    base = FrankensteinEngine(tmp_path / "base", origin)
    eid = base.create_expectation("Alex will return the book", actor_id="alex", confidence=0.8)
    shutil.copytree(base.home, tmp_path / "confirmed")
    shutil.copytree(base.home, tmp_path / "violated")
    confirmed = FrankensteinEngine.open(tmp_path / "confirmed")
    violated = FrankensteinEngine.open(tmp_path / "violated")
    confirmed.update_expectation(eid, "confirmed")
    violated.update_expectation(eid, "violated")
    assert confirmed.relationship("alex")["trust"] > violated.relationship("alex")["trust"]
    assert violated.relationship("alex")["resentment"] > confirmed.relationship("alex")["resentment"]


def test_unknown_expectation_update_fails(engine):
    with pytest.raises(ValueError, match="unknown expectation"):
        engine.update_expectation("missing", "violated")
