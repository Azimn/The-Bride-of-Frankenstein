from __future__ import annotations

from pathlib import Path
import shutil
import tempfile

from .backup import create_backup, restore_backup
from .cartridge import CharacterOrigin
from .decision import ActionCandidate
from .engine import FrankensteinEngine
from .firewall import assert_subjective_safe
from .renderer import DeterministicRenderer
from .types import Authority, Canonicality, EventKind, WorldEvent


class EvaluationFailure(AssertionError):
    pass


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise EvaluationFailure(message)


def sample_origin() -> CharacterOrigin:
    return CharacterOrigin(
        entity_id="sample-character",
        display_name="Ada",
        traits={"curiosity": 0.6, "caution": 0.2},
        values={"honesty": 0.8, "autonomy": 0.8},
        voice=("Prefer concise sentences.", "Do not claim memories that are not present."),
        action_priors={"engage": 0.03},
    )


def run_acceptance() -> list[str]:
    passed: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        origin = sample_origin()
        engine = FrankensteinEngine(root / "main", origin, renderer=DeterministicRenderer())

        w = engine.observe(WorldEvent("A red lamp is switched on.", tags=("lamp", "red"), salience=0.7))
        _expect(engine.status()["integrity_ok"], "ledger integrity failed")
        passed.append("ledger-integrity")

        try:
            engine.store.append_event(EventKind.BELIEF_UPDATE, Authority.RENDERER, {"x": 1})
            raise EvaluationFailure("renderer authored canonical belief")
        except ValueError:
            passed.append("renderer-authority-denied")

        proposal = engine.private_thought("Maybe the lamp means danger.", source_event_ids=(w.event_id,))
        _expect(proposal.canonicality == Canonicality.NONCANONICAL.value, "private thought was canonical")
        engine.admit_reflection(proposal.event_id, "The red lamp left me uneasy, but I do not know what it means.")
        passed.append("private-thought-admission")

        obs = engine.social_observation("jay", "I will help you tomorrow.", tags=("promise",))
        engine.set_belief("jay", "offered_help", True, confidence=0.7, evidence=(obs.event_id,))
        with engine.store.connect() as conn:
            _expect(conn.execute("SELECT COUNT(*) FROM beliefs").fetchone()[0] == 1, "belief projection missing")
        passed.append("evidence-backed-belief")

        c = engine.create_commitment("Check the workshop door", actor_id="jay")
        g = engine.create_goal("Finish the workshop inventory", priority=0.8)
        engine.set_concern("The workshop may not be secure", intensity=0.7)
        _expect(engine.status()["open_commitments"] == 1 and engine.status()["active_goals"] == 1, "prospective state missing")
        passed.append("prospective-state")

        cooperative = root / "cooperative"
        betrayed = root / "betrayed"
        shutil.copytree(root / "main", cooperative)
        shutil.copytree(root / "main", betrayed)
        a = FrankensteinEngine.open(cooperative)
        b = FrankensteinEngine.open(betrayed)
        a.update_relationship("jay", {"trust": 0.8, "attachment": 0.3})
        b.update_relationship("jay", {"trust": -0.8, "fear": 0.6, "resentment": 0.5})
        candidates = [
            ActionCandidate("accept_help", base_utility=0.2, relationship_weights={"trust": 0.8}),
            ActionCandidate("keep_distance", base_utility=0.1, relationship_weights={"trust": -0.5, "fear": 0.6}),
        ]
        ra = a.decide(candidates, actor_id="jay", context="jay offers help")
        rb = b.decide(candidates, actor_id="jay", context="jay offers help")
        _expect(ra.selected != rb.selected, "different histories did not alter decision")
        passed.append("path-dependence")

        frame = b.subjective_frame(actor_id="jay", situation="Jay is here.", selected_move="keep_distance", memory_query="Jay")
        assert_subjective_safe(frame)
        _expect("0.8" not in str(frame.as_prompt_dict()), "raw relationship float leaked")
        passed.append("subjective-firewall")

        before = engine.store.projection_digest()
        engine.projections.rebuild()
        after = engine.store.projection_digest()
        _expect(before == after, "replay did not reconstruct identical projections")
        passed.append("replay-equivalence")

        reopened = FrankensteinEngine.open(root / "main")
        _expect(reopened.status()["projection_digest"] == after, "restart changed state")
        passed.append("restart-continuity")

        backup = create_backup(engine, root / "backup.tgz")
        restored = restore_backup(backup, root / "restored")
        _expect(restored.store.verify_integrity().ok, "restored ledger invalid")
        _expect(restored.store.projection_digest() == engine.store.projection_digest(), "restored projection differs")
        passed.append("backup-restore")

        denied = ActionCandidate("send_message", required_capability="send_message")
        try:
            engine.execute_action(denied, {"text": "hello"})
            raise EvaluationFailure("unregistered capability executed")
        except PermissionError:
            passed.append("capability-gate")

        engine.record_outcome("engage", reward=1.0, summary="The conversation went well.")
        r1 = engine.decide([ActionCandidate("engage", 0.1), ActionCandidate("withdraw", 0.1)])
        _expect(r1.scores["engage"] > r1.scores["withdraw"], "reinforcement did not influence future action")
        passed.append("experience-learning")

        hits = engine.memory.search("red lamp", top_k=3)
        _expect(any("red lamp" in h.text.lower() for h in hits), "memory retrieval missed relevant experience")
        passed.append("memory-retrieval")

        response = engine.chat("jay", "Are you still thinking about the workshop?")
        _expect(bool(response.strip()), "chat produced no output")
        with engine.store.connect() as conn:
            _expect(conn.execute("SELECT COUNT(*) FROM events WHERE kind=? AND canonicality=?", (EventKind.RENDERER_OUTPUT.value, Canonicality.NONCANONICAL.value)).fetchone()[0] >= 1, "renderer output was not retained as noncanonical")
            _expect(conn.execute("SELECT COUNT(*) FROM events WHERE kind=? AND canonicality=?", (EventKind.SUBJECT_ACTION.value, Canonicality.CANONICAL.value)).fetchone()[0] >= 1, "subject action was not canonicalized")
        passed.append("renderer-separation")

        child_a = root / "branch-a"
        child_b = root / "branch-b"
        shutil.copytree(root / "main", child_a)
        shutil.copytree(root / "main", child_b)
        ca, cb = FrankensteinEngine.open(child_a), FrankensteinEngine.open(child_b)
        _expect(ca.store.projection_digest() == cb.store.projection_digest(), "clones did not start identical")
        ca.observe(WorldEvent("It starts raining.", tags=("weather",)))
        cb.observe(WorldEvent("The sun comes out.", tags=("weather",)))
        _expect(ca.store.projection_digest() != cb.store.projection_digest(), "divergent lives did not diverge")
        passed.append("branch-divergence")

    return passed
