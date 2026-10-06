from frankenstein.cartridge import CharacterOrigin
from frankenstein.decision import ActionCandidate
from frankenstein.engine import FrankensteinEngine


def engine(tmp_path):
    return FrankensteinEngine(
        tmp_path / "subject",
        CharacterOrigin(
            entity_id="v02-plan-subject",
            display_name="Ada",
        ),
    )


def test_plan_is_canonical_replayable_state(tmp_path):
    subject = engine(tmp_path)
    plan_id = subject.create_plan(
        "reach the archive",
        (("locked_gate",), ("ask_the_keeper",)),
    )

    state = subject.active_plan()
    assert state is not None
    assert state.plan_id == plan_id
    assert state.objective == "reach the archive"
    assert state.current_step == "locked_gate"

    before = state.payload()
    subject.rebuild()
    after = subject.active_plan()

    assert after is not None
    assert after.payload() == before
    assert subject.store.verify_integrity().ok


def test_plan_step_competes_through_existing_decision_engine(tmp_path):
    subject = engine(tmp_path)
    subject.create_plan(
        "reach the archive",
        (("ask_the_keeper",),),
    )

    receipt = subject.decide(
        [ActionCandidate("wait", base_utility=0.10)],
        context="reach the archive",
    )

    assert receipt.selected == "ask_the_keeper"
    assert "wait" in receipt.scores
    assert "ask_the_keeper" in receipt.scores


def test_plan_ablation_preserves_original_decision_path(tmp_path):
    subject = engine(tmp_path)
    subject.create_plan(
        "reach the archive",
        (("ask_the_keeper",),),
    )

    receipt = subject.decide(
        [ActionCandidate("wait", base_utility=0.10)],
        context="reach the archive",
        include_plan=False,
    )

    assert receipt.selected == "wait"
    assert "ask_the_keeper" not in receipt.scores


def test_stronger_homeostatic_pressure_can_beat_plan(tmp_path):
    subject = engine(tmp_path)
    subject.create_plan(
        "reach the archive",
        (("ask_the_keeper",),),
    )
    subject.update_need("energy", value=0.0)

    receipt = subject.decide(
        [
            ActionCandidate(
                "rest",
                base_utility=0.08,
                need_weights={"energy": 0.85},
            )
        ],
        context="reach the archive",
    )

    assert receipt.selected == "rest"
    assert subject.active_plan().current_step == "ask_the_keeper"


def test_failed_step_replans_and_survives_restart(tmp_path):
    subject = engine(tmp_path)
    plan_id = subject.create_plan(
        "reach the archive",
        (("locked_gate",), ("ask_the_keeper",)),
    )

    subject.record_plan_outcome(
        success=False,
        summary="The gate remained locked.",
        plan_id=plan_id,
    )

    assert subject.active_plan().current_step == "ask_the_keeper"

    reopened = FrankensteinEngine.open(subject.home)
    state = reopened.active_plan()
    assert state is not None
    assert state.current_step == "ask_the_keeper"
    assert state.status == "active"


def test_success_advances_steps_and_completes_goal(tmp_path):
    subject = engine(tmp_path)
    plan_id = subject.create_plan(
        "repair the relay",
        (("inspect_relay", "replace_fuse"),),
    )

    subject.record_plan_outcome(
        success=True,
        summary="Inspection completed.",
        plan_id=plan_id,
    )
    assert subject.active_plan().current_step == "replace_fuse"

    subject.record_plan_outcome(
        success=True,
        summary="The fuse was replaced.",
        plan_id=plan_id,
    )

    state = subject.active_plan()
    assert state is not None
    assert state.status == "completed"
    assert state.current_step is None

    with subject.store.connect() as conn:
        goal = conn.execute(
            "SELECT status FROM goals WHERE goal_id=?",
            (state.goal_id,),
        ).fetchone()
    assert goal["status"] == "completed"


def test_exhausted_routes_end_plan_instead_of_looping(tmp_path):
    subject = engine(tmp_path)
    plan_id = subject.create_plan(
        "reach the archive",
        (("locked_gate",), ("ask_the_keeper",)),
    )

    subject.record_plan_outcome(
        success=False,
        summary="The gate remained locked.",
        plan_id=plan_id,
    )
    subject.record_plan_outcome(
        success=False,
        summary="The keeper refused access.",
        plan_id=plan_id,
    )

    state = subject.active_plan()
    assert state is not None
    assert state.status == "abandoned"
    assert state.current_step is None


def test_plan_bounds_reject_unbounded_route_sets(tmp_path):
    subject = engine(tmp_path)
    routes = tuple((f"route_{i}",) for i in range(9))

    try:
        subject.create_plan("too many routes", routes)
    except ValueError:
        pass
    else:
        raise AssertionError("unbounded route count should be rejected")


def test_only_one_active_plan_can_exist(tmp_path):
    subject = engine(tmp_path)
    subject.create_plan("first goal", (("step_a",),))

    try:
        subject.create_plan("second goal", (("step_b",),))
    except ValueError:
        pass
    else:
        raise AssertionError("second active plan should be rejected")
