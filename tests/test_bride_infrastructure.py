from bride.mechanisms.frame_receipt import build_subjective_frame_receipt
from bride.mechanisms.renderer_benchmark import (
    compare,
    semantic_projection_from_engine,
)
from frankenstein.cartridge import CharacterOrigin
from frankenstein.engine import FrankensteinEngine
from frankenstein.types import WorldEvent


def engine(tmp_path):
    return FrankensteinEngine(
        tmp_path / "subject",
        CharacterOrigin(
            entity_id="bride-infrastructure-subject",
            display_name="Ada",
        ),
    )


def test_subjective_frame_receipt_binds_real_ledger_and_retrieval(tmp_path):
    subject = engine(tmp_path)
    world = subject.observe(
        WorldEvent(
            "A brass key is left on the desk.",
            actor_id="jay",
            tags=("brass", "key"),
        )
    )
    hits = subject.memory.search("brass key", actor_id="jay", top_k=2)

    receipt = build_subjective_frame_receipt(
        subject,
        actor_id="jay",
        renderer_id="deterministic-v1",
        retrieved_hits=hits,
        retrieval_budget=2,
    )

    assert receipt.canonical_source_seq == subject.store.max_seq()
    assert receipt.canonical_tail_hash == subject.store.iter_events(canonical_only=True)[-1].event_hash
    assert receipt.actor_id == "jay"
    assert receipt.retrieval_budget == 2
    assert world.event_id in {
        subject.store.event(source_id).cause_ids[0]
        if subject.store.event(source_id) and subject.store.event(source_id).cause_ids
        else source_id
        for source_id in receipt.retrieved_source_event_ids
    }


def test_receipt_changes_when_canonical_head_changes(tmp_path):
    subject = engine(tmp_path)
    hits = subject.memory.search("nothing", top_k=1)
    before = build_subjective_frame_receipt(
        subject,
        actor_id=None,
        renderer_id="deterministic-v1",
        retrieved_hits=hits,
        retrieval_budget=1,
    )
    subject.observe(WorldEvent("A bell rings."))
    after = build_subjective_frame_receipt(
        subject,
        actor_id=None,
        renderer_id="deterministic-v1",
        retrieved_hits=subject.memory.search("bell", top_k=1),
        retrieval_budget=1,
    )

    assert before.digest() != after.digest()
    assert before.canonical_tail_hash != after.canonical_tail_hash


def test_receipt_instrumentation_is_not_first_person_content(tmp_path):
    subject = engine(tmp_path)
    frame = subject.subjective_frame(
        actor_id=None,
        situation="A quiet room.",
        selected_move="engage",
        memory_query="room",
    )
    payload = str(frame.as_prompt_dict()).lower()

    assert "canonical_tail_hash" not in payload
    assert "retrieval_policy_version" not in payload
    assert "source_event_id" not in payload


def test_renderer_swap_uses_real_renderer_independent_state(tmp_path):
    subject = engine(tmp_path)
    subject.update_relationship("jay", {"trust": 0.4})
    subject.create_commitment("Return the key", actor_id="jay")
    subject.create_goal("Inspect the desk", priority=0.7)

    control = semantic_projection_from_engine(
        subject,
        actor_id="jay",
        selected_action="engage",
    )
    challenger = semantic_projection_from_engine(
        subject,
        actor_id="jay",
        selected_action="engage",
    )
    result = compare(
        control,
        challenger,
        "I am here and paying attention.",
        "I'm listening.",
    )

    assert result.semantic_equal
    assert not result.surface_equal
