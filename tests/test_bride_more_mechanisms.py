from datetime import datetime, timedelta, timezone

from bride.mechanisms.affect6d import Affect6D
from bride.mechanisms.involuntary import InvoluntaryExpressionGate
from bride.mechanisms.offscreen import OffscreenCatchupClock
from bride.mechanisms.plastic_policy import ContextualPlasticPolicy
from bride.mechanisms.renderer_benchmark import SemanticProjection, compare


def test_offscreen_catchup_is_bounded_and_retains_deferred_time(tmp_path):
    clock = OffscreenCatchupClock(tmp_path / "clock.json", tick_minutes=60, max_minutes_per_run=180)
    start = datetime(2026, 10, 1, tzinfo=timezone.utc)
    clock.initialize(start)
    result = clock.catch_up(start + timedelta(hours=10))
    assert result.elapsed_minutes == 600
    assert result.applied_minutes == 180
    assert result.deferred_minutes == 420
    assert result.ticks == (60.0, 60.0, 60.0)


def test_renderer_benchmark_separates_semantics_from_surface():
    p = SemanticProjection("id", (("trust", 0.2),), ("keep secret",), ("repair",), "decline")
    result = compare(p, p, "No.", "I will not disclose it.")
    assert result.semantic_equal
    assert not result.surface_equal


def test_6d_novelty_can_add_caution_but_is_not_itself_evidence_of_superiority():
    state = Affect6D().updated(novelty=0.8, dominance=-0.2)
    assert state.caution_pressure() > 0


def test_contextual_plastic_policy_can_learn_opposite_actions_by_context():
    p = ContextualPlasticPolicy()
    for _ in range(8):
        p.learn("safe", "approach", 1.0)
        p.learn("safe", "avoid", -1.0)
        p.learn("danger", "approach", -1.0)
        p.learn("danger", "avoid", 1.0)
    assert p.choose("safe", ("approach", "avoid")) == "approach"
    assert p.choose("danger", ("approach", "avoid")) == "avoid"


def test_involuntary_expression_is_not_intentional_speech():
    result = InvoluntaryExpressionGate().evaluate(pain=0.9)
    assert result is not None
    assert result.action == "pain_vocalization"
    assert not result.intentional
