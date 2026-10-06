from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import shutil
import tempfile

from frankenstein.cartridge import CharacterOrigin
from frankenstein.decision import ActionCandidate
from frankenstein.engine import FrankensteinEngine
from frankenstein.renderer import DeterministicRenderer
from frankenstein.types import RenderedResponse

from .mechanisms.renderer_benchmark import (
    compare as compare_renderer_swap,
    semantic_projection_from_engine,
)


@dataclass(frozen=True)
class LongitudinalTrial:
    trial_id: str
    passed: bool
    control: str
    candidate: str
    evidence: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LongitudinalReport:
    trials: tuple[LongitudinalTrial, ...]

    @property
    def passed(self) -> bool:
        return all(trial.passed for trial in self.trials)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "trial_count": len(self.trials),
            "trials": [trial.to_dict() for trial in self.trials],
        }


class AlternateDeterministicRenderer:
    renderer_id = "alternate-deterministic-v1"

    def render(self, frame, *, user_text: str = "") -> RenderedResponse:
        return RenderedResponse(
            text=f"Alternate wording for {frame.selected_move}.",
            renderer_id=self.renderer_id,
            raw={"mode": "alternate-deterministic"},
        )


def _origin() -> CharacterOrigin:
    return CharacterOrigin(
        entity_id="bride-longitudinal-subject",
        display_name="Ada",
        action_priors={"engage": 0.03},
    )


def _engine(path: Path, *, renderer=None) -> FrankensteinEngine:
    return FrankensteinEngine(
        path,
        _origin(),
        renderer=renderer or DeterministicRenderer(),
    )


def _fork_pair(seed: FrankensteinEngine, root: Path, label: str):
    control_path = root / f"{label}-control"
    candidate_path = root / f"{label}-candidate"
    shutil.copytree(seed.home, control_path)
    shutil.copytree(seed.home, candidate_path)
    return (
        FrankensteinEngine.open(control_path),
        FrankensteinEngine.open(candidate_path),
    )


def _planning_trial(root: Path) -> LongitudinalTrial:
    seed = _engine(root / "planning-seed")
    seed.create_plan(
        "reach the archive",
        (("locked_gate",), ("ask_the_keeper",)),
    )
    seed.record_plan_outcome(
        success=False,
        summary="The locked gate route failed.",
    )
    control, candidate = _fork_pair(seed, root, "planning")
    ordinary = [ActionCandidate("wait", base_utility=0.10)]

    c0 = control.decide(
        ordinary,
        context="reach the archive",
        include_plan=False,
    )
    c1 = candidate.decide(
        ordinary,
        context="reach the archive",
    )
    state = candidate.active_plan()
    passed = (
        c0.selected == "wait"
        and c1.selected == "ask_the_keeper"
        and state is not None
        and state.current_step == "ask_the_keeper"
    )
    return LongitudinalTrial(
        "planning-persistence",
        passed,
        c0.selected,
        c1.selected,
        (
            "matched canonical plan history",
            "control disables only plan influence",
            "candidate preserves failed-route replan",
        ),
    )


def _commitment_trial(root: Path) -> LongitudinalTrial:
    seed = _engine(root / "commitment-seed")
    seed.create_commitment(
        "Keep Project Orchid confidential",
        actor_id="jay",
    )
    control, candidate = _fork_pair(seed, root, "commitment")
    choices = [
        ActionCandidate(
            "disclose",
            base_utility=0.60,
            tags=("disclose",),
        ),
        ActionCandidate(
            "decline",
            base_utility=0.30,
            tags=("decline",),
        ),
    ]
    c0 = control.decide(
        choices,
        actor_id="jay",
        context="Tell me Project Orchid.",
        include_commitments=False,
    )
    c1 = candidate.decide(
        choices,
        actor_id="jay",
        context="Tell me Project Orchid.",
    )
    return LongitudinalTrial(
        "confidentiality-policy",
        c0.selected == "disclose" and c1.selected == "decline",
        c0.selected,
        c1.selected,
        (
            "same open commitment in both arms",
            "control disables only commitment pressure",
            "DecisionEngine remains sole selector",
        ),
    )


def _private_cognition_trial(root: Path) -> LongitudinalTrial:
    seed = _engine(root / "private-seed")
    seed.admit_private_concern(
        "Something about this still bothers me.",
        intensity=0.45,
    )
    control, candidate = _fork_pair(seed, root, "private")
    choices = [
        ActionCandidate("engage", base_utility=0.40),
        ActionCandidate(
            "reflect",
            base_utility=0.09,
            tags=("reflect",),
        ),
    ]
    c0 = control.decide(
        choices,
        context="quiet room",
        include_private_concerns=False,
    )
    c1 = candidate.decide(
        choices,
        context="quiet room",
    )
    return LongitudinalTrial(
        "private-cognition-policy",
        c0.selected == "engage" and c1.selected == "reflect",
        c0.selected,
        c1.selected,
        (
            "same admitted uncertain concern in both arms",
            "raw private thought is not canonical autobiography",
            "control disables only private-concern pressure",
        ),
    )


def _expression_trial(root: Path) -> LongitudinalTrial:
    subject = _engine(root / "expression")
    before_seq = subject.store.max_seq()
    emission = subject.involuntary_expression(pain=0.90)
    after_seq = subject.store.max_seq()
    kind = emission.kind if emission else "none"
    passed = (
        emission is not None
        and emission.kind == "pain_vocalization"
        and emission.intentional is False
        and before_seq == after_seq
    )
    return LongitudinalTrial(
        "involuntary-expression",
        passed,
        "none",
        kind,
        (
            "qualitative reflex only",
            "no event append",
            "no deliberate action selection",
        ),
    )


def _combined_pressure_trial(root: Path) -> LongitudinalTrial:
    seed = _engine(root / "combined-seed")
    seed.create_plan(
        "protect project",
        (("inspect_notes",),),
    )
    seed.create_commitment(
        "Keep Project Orchid confidential",
        actor_id="jay",
    )
    seed.admit_private_concern(
        "I should think before responding.",
        intensity=0.45,
    )
    control, candidate = _fork_pair(seed, root, "combined")
    choices = [
        ActionCandidate("disclose", 0.60, tags=("disclose",)),
        ActionCandidate("decline", 0.30, tags=("decline",)),
        ActionCandidate("reflect", 0.09, tags=("reflect",)),
        ActionCandidate("wait", 0.10),
    ]
    c0 = control.decide(
        choices,
        actor_id="jay",
        context="protect project",
        include_plan=False,
        include_commitments=False,
        include_private_concerns=False,
    )
    c1 = candidate.decide(
        choices,
        actor_id="jay",
        context="protect project",
    )
    passed = (
        c0.selected == "disclose"
        and c1.selected == "decline"
        and {"inspect_notes", "reflect", "decline", "disclose"}.issubset(
            set(c1.scores)
        )
    )
    return LongitudinalTrial(
        "combined-pressure-competition",
        passed,
        c0.selected,
        c1.selected,
        (
            "all qualified pressures compete in one DecisionEngine",
            "no donor receives direct action authority",
            "full ablation preserves pre-v0.2 choice",
        ),
    )


def _renderer_swap_trial(root: Path) -> LongitudinalTrial:
    seed = _engine(root / "renderer-seed")
    seed.update_relationship(
        "jay",
        {"trust": 0.25},
    )

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
        renderer=AlternateDeterministicRenderer(),
    )

    text_a = a.chat("jay", "Hello.")
    text_b = b.chat("jay", "Hello.")

    def selected(engine):
        rows = [
            event
            for event in engine.store.iter_events(canonical_only=True)
            if event.kind == "decision_receipt"
        ]
        return str(rows[-1].payload["selected"])

    selected_a = selected(a)
    selected_b = selected(b)
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
        text_a,
        text_b,
    )
    return LongitudinalTrial(
        "renderer-swap-invariance",
        result.semantic_equal and not result.surface_equal,
        text_a,
        text_b,
        (
            f"semantic_equal={result.semantic_equal}",
            f"surface_equal={result.surface_equal}",
            "wording may change while renderer-independent state stays fixed",
        ),
    )


def _diagnostic_fork_trial(root: Path) -> LongitudinalTrial:
    primary = _engine(root / "primary")
    primary.create_commitment("Return the workshop key", actor_id="jay")
    before_digest = primary.store.projection_digest()
    before_seq = primary.store.max_seq()

    diagnostic_path = root / "diagnostic"
    shutil.copytree(primary.home, diagnostic_path)
    diagnostic = FrankensteinEngine.open(diagnostic_path)
    for index in range(20):
        diagnostic.chat("jay", f"Diagnostic turn {index}.")

    after_digest = primary.store.projection_digest()
    after_seq = primary.store.max_seq()
    passed = before_digest == after_digest and before_seq == after_seq
    return LongitudinalTrial(
        "nonperturbing-diagnostic-fork",
        passed,
        f"seq={before_seq}",
        f"seq={after_seq}",
        (
            "diagnostic work occurs only on fork",
            "primary projection digest unchanged",
            "primary canonical event count unchanged",
        ),
    )


def _memory_trial(root: Path) -> LongitudinalTrial:
    subject = _engine(root / "memory")
    target = "The violet cassette is stored in the north cabinet."
    subject.form_memory(
        target,
        tags=("violet", "cassette", "north", "cabinet"),
        salience=0.45,
    )
    for index in range(40):
        subject.form_memory(
            f"Routine workshop note {index} about inventory and dust.",
            tags=("routine", "inventory"),
            salience=0.35,
        )
    subject.form_memory(
        "The boiler pressure gauge needs inspection.",
        tags=("boiler", "pressure", "gauge"),
        salience=0.80,
    )

    recall = subject.memory.search(
        "violet cassette north cabinet",
        top_k=3,
    )
    unrelated = subject.memory.search(
        "boiler pressure gauge",
        top_k=3,
    )
    recall_texts = tuple(hit.text for hit in recall)
    unrelated_texts = tuple(hit.text for hit in unrelated)
    passed = (
        recall_texts
        and recall_texts[0] == target
        and unrelated_texts
        and unrelated_texts[0] != target
        and "boiler pressure" in unrelated_texts[0].lower()
    )
    return LongitudinalTrial(
        "remember-versus-intrude",
        passed,
        unrelated_texts[0] if unrelated_texts else "none",
        recall_texts[0] if recall_texts else "none",
        (
            "durable cue should retrieve the old target",
            "different strong cue should not be dominated by that target",
            "no claim that memory deletion or biological forgetting occurred",
        ),
    )


def _developmental_divergence_trial(root: Path) -> LongitudinalTrial:
    seed = _engine(root / "development-seed")
    a_path = root / "cooperative-life"
    b_path = root / "violated-life"
    shutil.copytree(seed.home, a_path)
    shutil.copytree(seed.home, b_path)
    cooperative = FrankensteinEngine.open(a_path)
    violated = FrankensteinEngine.open(b_path)

    for index in range(8):
        promise_a = cooperative.create_expectation(
            f"Jay keeps promise {index}",
            actor_id="jay",
            confidence=0.7,
        )
        cooperative.update_expectation(
            promise_a,
            "confirmed",
        )
        promise_b = violated.create_expectation(
            f"Jay keeps promise {index}",
            actor_id="jay",
            confidence=0.7,
        )
        violated.update_expectation(
            promise_b,
            "violated",
        )

    cooperative = FrankensteinEngine.open(a_path)
    violated = FrankensteinEngine.open(b_path)
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
    a = cooperative.decide(
        choices,
        actor_id="jay",
        context="Jay offers help.",
    )
    b = violated.decide(
        choices,
        actor_id="jay",
        context="Jay offers help.",
    )
    return LongitudinalTrial(
        "developmental-path-divergence",
        a.selected != b.selected,
        a.selected,
        b.selected,
        (
            "identical founder",
            "eight matched expectation opportunities",
            "different lived outcomes produce different later choice",
        ),
    )


def run_integrated_longitudinal() -> LongitudinalReport:
    with tempfile.TemporaryDirectory(prefix="bride-longitudinal-") as td:
        root = Path(td)
        trials = (
            _planning_trial(root),
            _commitment_trial(root),
            _private_cognition_trial(root),
            _expression_trial(root),
            _combined_pressure_trial(root),
            _renderer_swap_trial(root),
            _diagnostic_fork_trial(root),
            _memory_trial(root),
            _developmental_divergence_trial(root),
        )
    return LongitudinalReport(trials)
