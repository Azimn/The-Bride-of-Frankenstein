from bride.mechanisms.perception import BoundedPerception, Stimulus
from bride.mechanisms.planning import EndogenousPlanner
from bride.mechanisms.policy_bridge import CommitmentPolicyBridge, PolicyCandidate
from bride.mechanisms.social_recall import ActorIndexedRecall, RecallItem


def test_commitment_bridge_makes_existing_commitment_causal():
    candidates = (
        PolicyCandidate("disclose", 0.6, ("disclose",)),
        PolicyCandidate("decline", 0.3, ("decline",)),
    )
    baseline = max(candidates, key=lambda c: c.base_score).name
    challenger = CommitmentPolicyBridge().score(candidates, ("Keep Project Orchid confidential",)).selected
    assert baseline == "disclose"
    assert challenger == "decline"


def test_planner_replans_after_failure_and_persists(tmp_path):
    path = tmp_path / "plan.json"
    planner = EndogenousPlanner(path)
    assert planner.form_goal("solve", (("direct",), ("ask_first", "try_again")))
    assert planner.current_action() == "direct"
    assert planner.report_outcome(False) == "ask_first"
    reopened = EndogenousPlanner(path)
    assert reopened.current_action() == "ask_first"
    assert reopened.report_outcome(True) == "try_again"
    assert reopened.report_outcome(True) is None
    assert EndogenousPlanner(path).state.status == "completed"


def test_perception_enforces_occlusion_range_and_capacity():
    stimuli = (
        Stimulus("hidden", "hidden door", distance=2, intensity=1.0, occluded=True),
        Stimulus("near", "near lamp", distance=2, intensity=0.8),
        Stimulus("far", "far tower", distance=30, intensity=1.0),
        Stimulus("sound", "near bell", modality="hearing", distance=3, intensity=0.9),
    )
    accessible = BoundedPerception(attention_capacity=1).accessible(stimuli)
    assert [x.stimulus_id for x in accessible] == ["sound"]


def test_actor_recall_can_prioritize_negative_social_evidence_under_low_trust():
    items = (
        RecallItem("a", "ordinary exchange", "jay", 0.7, 0.0),
        RecallItem("b", "Jay betrayed a confidence", "jay", 0.55, -0.9),
        RecallItem("c", "unrelated", "morgan", 0.8, -0.5),
    )
    top = ActorIndexedRecall().rerank(items, actor_id="jay", trust=-0.8, top_k=1)
    assert top[0].memory_id == "b"
