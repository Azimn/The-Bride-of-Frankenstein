from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path
import tempfile

from .contracts import DonorRole
from .fake_subject import DeterministicLabSubject
from .mechanisms.reference import donor
from .qualification import QualificationHarness
from .registry import DONORS, DONOR_BY_ID
from .scenarios import CASES, HISTORIES, PROBES


REAL_EXECUTABLE_CASES = {
    "duck_endogenous_planning",
    "jelly_private_cognition_feedback",
    "tiny_persona_perception",
    "pretorius_v6_recall_social",
    "doctor_lives_commitment_policy_bridge",
    "digital_subject_continuity_influence",
    "bounded_offscreen_catchup",
    "first_person_involuntary_expression",
    "omnicore_six_dimensional_affect",
    "recurrent_plastic_policy",
}


def _payload(mechanism_id: str) -> dict:
    if mechanism_id == "jelly_private_cognition_feedback":
        return {"thought": "Something about this still bothers me."}
    return {}


def _subject(real_frankenstein: bool):
    if not real_frankenstein:
        return DeterministicLabSubject()

    from frankenstein.cartridge import CharacterOrigin
    from .frankenstein_adapter import FrankensteinSubjectAdapter

    root = tempfile.mkdtemp(prefix="bride-real-")
    return FrankensteinSubjectAdapter.create(
        root,
        CharacterOrigin(
            entity_id="bride-qualification-subject",
            display_name="Ada",
        ),
    )


def _result_dict(result) -> dict:
    return {
        "mechanism_id": result.mechanism_id,
        "verdict": result.verdict.value,
        "causal_effect": result.causal_effect,
        "consistency": result.consistency,
        "specificity": result.specificity,
        "baseline_quality": result.baseline_quality,
        "challenger_quality": result.challenger_quality,
        "quality_gain": result.quality_gain,
        "truth_preserved": result.truth_preserved,
        "authority_preserved": result.authority_preserved,
        "replay_preserved": result.replay_preserved,
        "identity_preserved": result.identity_preserved,
        "renderer_invariant": result.renderer_invariant,
        "baseline_latency_ms": result.baseline_latency_ms,
        "challenger_latency_ms": result.challenger_latency_ms,
        "latency_delta_ms": result.latency_delta_ms,
        "latency_ratio": result.latency_ratio,
        "state_size_ratio": result.state_size_ratio,
        "passed_cases": list(result.passed_cases),
        "failed_cases": list(result.failed_cases),
        "reasons": list(result.reasons),
    }


def _run_one(mechanism_id: str, *, real_frankenstein: bool):
    spec = DONOR_BY_ID[mechanism_id]
    cases = CASES.get(mechanism_id, ())

    if real_frankenstein and cases and mechanism_id not in REAL_EXECUTABLE_CASES:
        return {
            "mechanism_id": mechanism_id,
            "verdict": "unqualified",
            "reasons": ["no frozen real-Frankenstein adapter case exists yet"],
        }

    if not cases and spec.role not in {DonorRole.EVALUATION, DonorRole.PROVENANCE} and not spec.requires_model:
        return {
            "mechanism_id": mechanism_id,
            "verdict": "unqualified",
            "reasons": ["registered donor has no frozen qualification case yet"],
        }

    result = QualificationHarness().run(
        _subject(real_frankenstein),
        donor(mechanism_id, **_payload(mechanism_id)),
        cases,
        HISTORIES,
        PROBES,
    )
    return _result_dict(result)


def main(argv=None):
    parser = ArgumentParser(prog="bride-qualify")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")

    run = sub.add_parser("run")
    run.add_argument("mechanism_id")
    run.add_argument("--real-frankenstein", action="store_true")

    suite = sub.add_parser("suite")
    suite.add_argument("--real-frankenstein", action="store_true")
    suite.add_argument("--output")

    args = parser.parse_args(argv)

    if args.cmd == "list":
        print(json.dumps([
            {
                "id": d.mechanism_id,
                "donor": d.donor,
                "role": d.role.value,
                "title": d.title,
                "complexity_points": d.complexity_points,
                "requires_model": d.requires_model,
            }
            for d in DONORS
        ], indent=2))
        return

    if args.cmd == "run":
        if args.mechanism_id not in DONOR_BY_ID:
            raise SystemExit(f"unknown mechanism {args.mechanism_id}")
        payload = _run_one(
            args.mechanism_id,
            real_frankenstein=args.real_frankenstein,
        )
        print(json.dumps(payload, indent=2))
        return

    results = [
        _run_one(d.mechanism_id, real_frankenstein=args.real_frankenstein)
        for d in DONORS
    ]
    payload = {
        "baseline": "Azimn/Frankenstein@fdaf5be89ccf6991a20eb54649d5318a9adcb6ff",
        "real_frankenstein": bool(args.real_frankenstein),
        "governing_question": (
            "Does changing this internal state predictably change what the same individual "
            "attends to, remembers, predicts, learns, decides, or does later, while preserving "
            "historical truth and architectural authority?"
        ),
        "results": results,
    }

    rendered = json.dumps(payload, indent=2) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
