from __future__ import annotations

from argparse import ArgumentParser
import json
import tempfile

from .fake_subject import DeterministicLabSubject
from .mechanisms.reference import donor
from .qualification import QualificationHarness
from .registry import DONORS, DONOR_BY_ID
from .scenarios import CASES, HISTORIES, PROBES


def _payload(mechanism_id: str) -> dict:
    if mechanism_id == "jelly_private_cognition_feedback":
        return {"thought": "Something about this still bothers me."}
    return {}


def main(argv=None):
    parser = ArgumentParser(prog="bride-qualify")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    run = sub.add_parser("run")
    run.add_argument("mechanism_id")
    run.add_argument("--real-frankenstein", action="store_true")
    args = parser.parse_args(argv)

    if args.cmd == "list":
        print(json.dumps([{"id": d.mechanism_id, "donor": d.donor, "role": d.role.value, "title": d.title} for d in DONORS], indent=2))
        return

    spec = DONOR_BY_ID[args.mechanism_id]
    if args.mechanism_id not in CASES:
        raise SystemExit(f"{args.mechanism_id} is registered as {spec.role.value} but has no deterministic qualification case yet")

    if args.real_frankenstein:
        from frankenstein.cartridge import CharacterOrigin
        from .frankenstein_adapter import FrankensteinSubjectAdapter
        root = tempfile.mkdtemp(prefix="bride-real-")
        subject = FrankensteinSubjectAdapter.create(
            root,
            CharacterOrigin(entity_id="bride-qualification-subject", display_name="Ada"),
        )
    else:
        subject = DeterministicLabSubject()

    result = QualificationHarness().run(
        subject,
        donor(args.mechanism_id, **_payload(args.mechanism_id)),
        CASES[args.mechanism_id],
        HISTORIES,
        PROBES,
    )
    print(json.dumps({
        "mechanism_id": result.mechanism_id,
        "verdict": result.verdict.value,
        "causal_effect": result.causal_effect,
        "consistency": result.consistency,
        "specificity": result.specificity,
        "truth_preserved": result.truth_preserved,
        "authority_preserved": result.authority_preserved,
        "replay_preserved": result.replay_preserved,
        "identity_preserved": result.identity_preserved,
        "latency_ratio": result.latency_ratio,
        "state_size_ratio": result.state_size_ratio,
        "passed_cases": result.passed_cases,
        "failed_cases": result.failed_cases,
        "reasons": result.reasons,
    }, indent=2))


if __name__ == "__main__":
    main()
