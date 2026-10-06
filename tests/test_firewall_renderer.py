from __future__ import annotations

from dataclasses import dataclass

import pytest

from frankenstein.decision import ActionCandidate
from frankenstein.firewall import assert_subjective_safe
from frankenstein.types import Canonicality, EventKind, RenderedResponse


@dataclass
class LoudRenderer:
    renderer_id: str = "loud"
    def render(self, frame, *, user_text=""):
        return RenderedResponse("ABSOLUTELY. " + user_text.upper(), self.renderer_id)


@dataclass
class QuietRenderer:
    renderer_id: str = "quiet"
    def render(self, frame, *, user_text=""):
        return RenderedResponse("I hear you.", self.renderer_id)


def test_subjective_frame_contains_no_internal_markers(engine):
    engine.update_relationship("alex", {"trust": 0.55})
    frame = engine.subjective_frame(actor_id="alex", situation="Alex is nearby.", selected_move="engage")
    assert_subjective_safe(frame)
    text = str(frame.as_prompt_dict()).lower()
    assert "event_hash" not in text
    assert "source_event_id" not in text
    assert "utility_score" not in text


def test_renderer_swap_does_not_select_action(tmp_path, origin):
    a = __import__("frankenstein.engine", fromlist=["FrankensteinEngine"]).FrankensteinEngine(tmp_path / "a", origin, renderer=LoudRenderer())
    b = __import__("frankenstein.engine", fromlist=["FrankensteinEngine"]).FrankensteinEngine(tmp_path / "b", origin, renderer=QuietRenderer())
    for e in (a, b):
        e.update_relationship("alex", {"trust": -0.6, "fear": 0.6})
    choices = [
        ActionCandidate("engage", 0.1, relationship_weights={"trust": 0.8}),
        ActionCandidate("withdraw", 0.1, relationship_weights={"trust": -0.5, "fear": 0.8}),
    ]
    assert a.decide(choices, actor_id="alex").selected == b.decide(choices, actor_id="alex").selected == "withdraw"


def test_renderer_output_is_noncanonical_but_speech_action_is_canonical(tmp_path, origin):
    from frankenstein.engine import FrankensteinEngine
    engine = FrankensteinEngine(tmp_path / "home", origin, renderer=LoudRenderer())
    engine.chat("alex", "hello")
    events = engine.store.iter_events()
    rendered = [e for e in events if e.kind == EventKind.RENDERER_OUTPUT.value]
    actions = [e for e in events if e.kind == EventKind.SUBJECT_ACTION.value]
    assert rendered[-1].canonicality == Canonicality.NONCANONICAL.value
    assert actions[-1].canonicality == Canonicality.CANONICAL.value
    assert rendered[-1].event_id in actions[-1].cause_ids


def test_user_text_with_uuid_is_not_mistaken_for_internal_leak(engine):
    engine.social_observation("alex", "The ticket is 123e4567-e89b-12d3-a456-426614174000")
    frame = engine.subjective_frame(actor_id="alex", situation="Review the ticket.", selected_move="clarify", memory_query="ticket")
    assert_subjective_safe(frame)
