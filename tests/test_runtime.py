from __future__ import annotations

import pytest

from frankenstein.capabilities import CapabilityGate
from frankenstein.decision import ActionCandidate
from frankenstein.runtime import HeartbeatPolicy, HeartbeatRunner


def test_capability_gate_is_default_deny(engine):
    candidate = ActionCandidate("send", required_capability="send_message")
    with pytest.raises(PermissionError):
        engine.execute_action(candidate, {"text": "hello"})


def test_capability_gate_executes_registered_enabled_handler(tmp_path, origin):
    seen = []
    gate = CapabilityGate()
    gate.register("send_message", lambda payload: seen.append(payload["text"]) or "ok", enabled=True)
    from frankenstein.engine import FrankensteinEngine
    engine = FrankensteinEngine(tmp_path / "home", origin, capabilities=gate)
    candidate = ActionCandidate("send", required_capability="send_message")
    assert engine.execute_action(candidate, {"text": "hello"}) == "ok"
    assert seen == ["hello"]


def test_heartbeat_uses_decision_authority(engine):
    engine.update_need("energy", value=0.05)
    receipt = engine.heartbeat()
    assert receipt.selected == "rest"
    with engine.store.connect() as conn:
        row = conn.execute("SELECT value_json FROM runtime_state WHERE key='last_action'").fetchone()
    assert row is not None


def test_heartbeat_runner_is_bounded(engine):
    runner = HeartbeatRunner(engine, HeartbeatPolicy(interval_seconds=1.0, max_cycles=2))
    assert runner.run() == 2


def test_invalid_heartbeat_policy_fails():
    with pytest.raises(ValueError):
        HeartbeatPolicy(interval_seconds=0).validate()
