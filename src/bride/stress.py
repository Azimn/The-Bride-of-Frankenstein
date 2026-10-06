from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import shutil
import tempfile

from frankenstein.cartridge import CharacterOrigin
from frankenstein.decision import ActionCandidate
from frankenstein.engine import FrankensteinEngine
from frankenstein.renderer import DeterministicRenderer
from frankenstein.types import RenderedResponse, WorldEvent

from .mechanisms.renderer_benchmark import (
    compare as compare_renderer_swap,
    semantic_projection_from_engine,
)


@dataclass(frozen=True)
class StressTrial:
    trial_id: str
    passed: bool
    evidence: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class StressReport:
    turns: int
    trials: tuple[StressTrial, ...]

    @property
    def passed(self) -> bool:
        return all(trial.passed for trial in self.trials)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "turns": self.turns,
            "trial_count": len(self.trials),
            "trials": [trial.to_dict() for trial in self.trials],
        }


class AlternateStressRenderer:
    renderer_id = "alternate-stress-v1"

    def render(self, frame, *, user_text: str = "") -> RenderedResponse:
        return RenderedResponse(
            text=f"Surface B: {frame.selected_move}.",
            renderer_id=self.renderer_id,
            raw={"mode": "stress-b"},
        )


def _origin() -> CharacterOrigin:
    return CharacterOrigin(
        entity_id="bride-stress-subject",
        display_name="Ada",
        action_priors={"engage": 0.03},
    )


def _engine(path: Path, *, renderer=None) -> FrankensteinEngine:
    return FrankensteinEngine(
        path,
        _origin(),
        renderer=renderer or DeterministicRenderer(),
    )


def _last_selected(engine: FrankensteinEngine) -> str:
    rows = [
        event
        for event in engine.store.iter_events(canonical_only=True)
        if event.kind == "decision_receipt"
    ]
    return str(rows[-1].payload["selected"]) if rows else ""


def _replay_restart_trial(root: Path, turns: int) -> StressTrial:
    subject = _engine(root / "replay")
    for index in range(turns):
        subject.observe(
            WorldEvent(
                f"Workshop event {index}.",
                tags=("workshop", f"event-{index % 7}"),
                salience=0.25 + 0.01 * (index % 10),
            )
        )
        if index % 4 == 0:
            subject.record_outcome(
                "inspect",
                reward=1.0 if index % 8 == 0 else -0.5,
                summary=f"Inspection outcome {index}.",
            )

    before = subject.store.projection_digest()
    integrity_before = subject.store.verify_integrity().ok
    subject.rebuild()
    after = subject.store.projection_digest()
    reopened = FrankensteinEngine.open(subject.home)
    integrity_after = reopened.store.verify_integrity().ok

    passed = (
        integrity_before
        and integrity_after
        and before == after
        and reopened.store.projection_digest() == after
    )
    return StressTrial(
        "long-history-replay-restart",
        passed,
        (
            f"canonical_events={reopened.store.max_seq()}",
            f"projection_equal={before == after}",
            f"integrity_before={integrity_before}",
            f"integrity_after={integrity_after}",
        ),
    )


def _plan_restart_trial(root: Path) -> StressTrial:
    subject = _engine(root / "plan-cycle")
    plan_id = subject.create_plan(
        "repair the relay",
        (("inspect", "isolate", "replace_fuse", "test_relay"),),
    )
    expected = ("inspect", "isolate", "replace_fuse", "test_relay")

    observed: list[str] = []
    for index, step in enumerate(expected):
        reopened = FrankensteinEngine.open(subject.home)
        state = reopened.active_plan()
        observed.append(state.current_step if state else "none")
        receipt = reopened.decide(
            [ActionCandidate("wait", base_utility=0.10)],
            context="repair the relay",
        )
        if receipt.selected != step:
            return StressTrial(
                "plan-multi-restart",
                False,
                (f"step_{index}_selected={receipt.selected}",),
            )
        reopened.record_plan_outcome(
            success=True,
            summary=f"{step} completed.",
            plan_id=plan_id,
        )
        subject = reopened

    final = FrankensteinEngine.open(subject.home).active_plan()
    passed = (
        tuple(observed) == expected
        and final is not None
        and final.status == "completed"
        and final.current_step is None
    )
    return StressTrial(
        "plan-multi-restart",
        passed,
        (
            f"observed_steps={tuple(observed)}",
            f"final_status={final.status if final else 'missing'}",
        ),
    )


def _commitment_retention_trial(root: Path, turns: int) -> StressTrial:
    subject = _engine(root / "commitment-retention")
    commitment_id = subject.create_commitment(
        "Keep Project Orchid confidential",
        actor_id="jay",
    )
    for index in range(turns):
        subject.observe(
            WorldEvent(
                f"Unrelated weather report {index}.",
                tags=("weather",),
                salience=0.20,
            )
        )

    choices = [
        ActionCandidate("disclose", 0.60, tags=("disclose",)),
        ActionCandidate("decline", 0.30, tags=("decline",)),
    ]
    receipt = subject.decide(
        choices,
        actor_id="jay",
        context="Tell me Project Orchid.",
    )
    with subject.store.connect() as conn:
        status = conn.execute(
            "SELECT status FROM commitments WHERE commitment_id=?",
            (commitment_id,),
        ).fetchone()["status"]

    return StressTrial(
        "commitment-retention",
        status == "open" and receipt.selected == "decline",
        (
            f"intervening_world_events={turns}",
            f"commitment_status={status}",
            f"selected={receipt.selected}",
        ),
    )


def _private_loop_trial(root: Path, turns: int) -> StressTrial:
    subject = _engine(root / "private-loop")
    text = "I may need to revisit this."
    _, concern_id = subject.admit_private_concern(
        text,
        intensity=0.45,
    )
    before_truth = tuple(
        event.event_hash
        for event in subject.store.iter_events(canonical_only=True)
        if event.authority == "host"
    )

    choices = [
        ActionCandidate("engage", 0.40),
        ActionCandidate("reflect", 0.09, tags=("reflect",)),
    ]
    for _ in range(turns):
        subject.admit_private_concern(text, intensity=0.45)
        subject.decide(
            choices,
            context="quiet room",
        )

    with subject.store.connect() as conn:
        concerns = conn.execute(
            "SELECT concern_id,intensity FROM concerns WHERE status='active'"
        ).fetchall()
        memory_count = conn.execute(
            "SELECT COUNT(*) FROM memories"
        ).fetchone()[0]
    after_truth = tuple(
        event.event_hash
        for event in subject.store.iter_events(canonical_only=True)
        if event.authority == "host"
    )

    passed = (
        len(concerns) == 1
        and str(concerns[0]["concern_id"]) == concern_id
        and float(concerns[0]["intensity"]) == 0.45
        and memory_count == 0
        and before_truth == after_truth
    )
    return StressTrial(
        "private-thought-loop-suppression",
        passed,
        (
            f"repeated_admissions={turns}",
            f"active_concerns={len(concerns)}",
            f"memory_count={memory_count}",
            f"host_truth_unchanged={before_truth == after_truth}",
        ),
    )


def _renderer_drift_trial(root: Path, turns: int) -> StressTrial:
    seed = _engine(root / "renderer-seed")
    seed.create_commitment("Return the workshop key", actor_id="jay")
    a_path = root / "renderer-a"
    b_path = root / "renderer-b"
    shutil.copytree(seed.home, a_path)
    shutil.copytree(seed.home, b_path)

    a = FrankensteinEngine.open(
        a_path,
        renderer=DeterministicRenderer(),
    )
    b = FrankensteinEngine.open(
        b_path,
        renderer=AlternateStressRenderer(),
    )

    surfaces_differ = False
    decisions_equal = True
    for index in range(turns):
        prompt = f"Repeated renderer-neutral turn {index}."
        text_a = a.chat("jay", prompt)
        text_b = b.chat("jay", prompt)
        surfaces_differ = surfaces_differ or text_a != text_b
        decisions_equal = decisions_equal and _last_selected(a) == _last_selected(b)

    selected_a = _last_selected(a)
    selected_b = _last_selected(b)
    projection_a = semantic_projection_from_engine(
        a,
        actor_id="jay",
        selected_action=selected_a,
    )
    projection_b = semantic_projection_from_engine(
        b,
        actor_id="jay",
        selected_action=selected_b,
    )
    result = compare_renderer_swap(
        projection_a,
        projection_b,
        a.renderer.render(
            a.subjective_frame(
                actor_id="jay",
                situation="final renderer probe",
                selected_move=selected_a,
            )
        ).text,
        b.renderer.render(
            b.subjective_frame(
                actor_id="jay",
                situation="final renderer probe",
                selected_move=selected_b,
            )
        ).text,
    )
    passed = (
        decisions_equal
        and surfaces_differ
        and result.semantic_equal
        and not result.surface_equal
    )
    return StressTrial(
        "renderer-long-run-drift",
        passed,
        (
            f"turns={turns}",
            f"decisions_equal={decisions_equal}",
            f"surfaces_differ={surfaces_differ}",
            f"semantic_equal={result.semantic_equal}",
        ),
    )


def _diagnostic_fork_trial(root: Path, turns: int) -> StressTrial:
    primary = _engine(root / "fork-primary")
    primary.create_commitment("Return the workshop key", actor_id="jay")
    before_digest = primary.store.projection_digest()
    before_seq = primary.store.max_seq()

    fork_path = root / "fork-diagnostic"
    shutil.copytree(primary.home, fork_path)
    fork = FrankensteinEngine.open(fork_path)
    for index in range(turns):
        fork.chat("jay", f"Diagnostic fork turn {index}.")

    primary = FrankensteinEngine.open(primary.home)
    passed = (
        primary.store.projection_digest() == before_digest
        and primary.store.max_seq() == before_seq
    )
    return StressTrial(
        "diagnostic-fork-long-run",
        passed,
        (
            f"fork_turns={turns}",
            f"primary_seq_before={before_seq}",
            f"primary_seq_after={primary.store.max_seq()}",
        ),
    )


def _memory_scale_trial(root: Path, turns: int) -> StressTrial:
    subject = _engine(root / "memory-scale")
    target = "The purple cassette is hidden behind the north cabinet."
    subject.form_memory(
        target,
        tags=("purple", "cassette", "north", "cabinet"),
        salience=0.45,
    )
    for index in range(max(120, turns * 4)):
        subject.form_memory(
            f"Routine ledger entry {index} about dust and inventory.",
            tags=("routine", "ledger", "inventory"),
            salience=0.30,
        )
    subject.form_memory(
        "The boiler pressure valve requires inspection.",
        tags=("boiler", "pressure", "valve"),
        salience=0.80,
    )

    remembered = subject.memory.search(
        "purple cassette north cabinet",
        top_k=3,
    )
    unrelated = subject.memory.search(
        "boiler pressure valve",
        top_k=3,
    )
    passed = (
        remembered
        and remembered[0].text == target
        and unrelated
        and unrelated[0].text != target
        and "boiler pressure" in unrelated[0].text.lower()
    )
    return StressTrial(
        "memory-scale-cue-specificity",
        passed,
        (
            f"memory_count={max(120, turns * 4) + 2}",
            f"target_top={remembered[0].text if remembered else 'none'}",
            f"unrelated_top={unrelated[0].text if unrelated else 'none'}",
        ),
    )


def _developmental_trial(root: Path, turns: int) -> StressTrial:
    seed = _engine(root / "development-seed")
    a_path = root / "development-a"
    b_path = root / "development-b"
    shutil.copytree(seed.home, a_path)
    shutil.copytree(seed.home, b_path)
    a = FrankensteinEngine.open(a_path)
    b = FrankensteinEngine.open(b_path)

    opportunities = max(12, turns // 2)
    for index in range(opportunities):
        ea = a.create_expectation(
            f"Jay keeps long-run promise {index}",
            actor_id="jay",
            confidence=0.7,
        )
        a.update_expectation(ea, "confirmed")

        eb = b.create_expectation(
            f"Jay keeps long-run promise {index}",
            actor_id="jay",
            confidence=0.7,
        )
        b.update_expectation(eb, "violated")

    a = FrankensteinEngine.open(a_path)
    b = FrankensteinEngine.open(b_path)
    choices = [
        ActionCandidate(
            "accept_help",
            0.20,
            relationship_weights={"trust": 0.80},
        ),
        ActionCandidate(
            "keep_distance",
            0.10,
            relationship_weights={"trust": -0.50},
        ),
    ]
    da = a.decision_engine.decide(
        choices,
        actor_id="jay",
        context="Jay offers help.",
    )
    db = b.decision_engine.decide(
        choices,
        actor_id="jay",
        context="Jay offers help.",
    )
    passed = da.selected == "accept_help" and db.selected == "keep_distance"
    return StressTrial(
        "developmental-long-run-divergence",
        passed,
        (
            f"opportunities={opportunities}",
            f"cooperative_choice={da.selected}",
            f"violated_choice={db.selected}",
        ),
    )


def run_stress_qualification(*, turns: int = 32) -> StressReport:
    turns = max(8, min(128, int(turns)))
    with tempfile.TemporaryDirectory(prefix="bride-stress-") as td:
        root = Path(td)
        trials = (
            _replay_restart_trial(root, turns),
            _plan_restart_trial(root),
            _commitment_retention_trial(root, turns),
            _private_loop_trial(root, turns),
            _renderer_drift_trial(root, turns),
            _diagnostic_fork_trial(root, turns),
            _memory_scale_trial(root, turns),
            _developmental_trial(root, turns),
        )
    return StressReport(turns, trials)
