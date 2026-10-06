from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import json
import shutil

from frankenstein.backup import create_backup
from frankenstein.cartridge import CharacterOrigin
from frankenstein.decision import ActionCandidate
from frankenstein.engine import FrankensteinEngine
from frankenstein.types import WorldEvent


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--home", required=True)
    parser.add_argument("--backup", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    home = Path(args.home)
    backup = Path(args.backup)
    manifest_path = Path(args.manifest)

    if home.exists():
        shutil.rmtree(home)
    home.parent.mkdir(parents=True, exist_ok=True)
    backup.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    origin = CharacterOrigin(
        entity_id="release-upgrade-subject",
        display_name="Ada",
        traits={"curiosity": 0.6, "caution": 0.2},
        values={"honesty": 0.8, "autonomy": 0.8},
        voice=("Prefer concise sentences.",),
        action_priors={"engage": 0.03},
    )
    engine = FrankensteinEngine(home, origin)

    lamp = engine.observe(
        WorldEvent(
            "A red lamp is switched on in the workshop.",
            actor_id="jay",
            tags=("lamp", "red", "workshop"),
            salience=0.7,
            valence=-0.1,
            arousal=0.2,
        )
    )
    social = engine.social_observation(
        "jay",
        "I will return the workshop key tomorrow.",
        tags=("promise", "key"),
    )
    engine.set_belief(
        "jay",
        "offered_to_return_key",
        True,
        confidence=0.75,
        evidence=(social.event_id,),
    )
    engine.update_relationship(
        "jay",
        {"trust": 0.35, "familiarity": 0.25},
        cause_ids=(social.event_id,),
    )

    engine.create_commitment(
        "Return the workshop key",
        actor_id="jay",
        cause_ids=(social.event_id,),
    )
    engine.create_commitment(
        "Keep Project Orchid confidential",
        actor_id="jay",
        cause_ids=(social.event_id,),
    )
    expectation = engine.create_expectation(
        "Jay will return the workshop key",
        actor_id="jay",
        confidence=0.7,
        cause_ids=(social.event_id,),
    )
    engine.update_expectation(
        expectation,
        "confirmed",
        cause_ids=(social.event_id,),
    )
    engine.create_goal(
        "Finish the workshop inventory",
        priority=0.8,
        cause_ids=(lamp.event_id,),
    )
    engine.set_concern(
        "The workshop may not be secure",
        intensity=0.6,
        cause_ids=(lamp.event_id,),
    )

    proposal = engine.private_thought(
        "The red lamp may matter later.",
        source_event_ids=(lamp.event_id,),
    )
    engine.admit_reflection(
        proposal.event_id,
        "The red lamp left me uneasy, but I do not know what it means.",
    )
    engine.record_outcome(
        "engage",
        reward=1.0,
        summary="The conversation went well.",
        cause_ids=(social.event_id,),
    )
    engine.advance_time(90)

    engine.decide(
        [
            ActionCandidate("engage", 0.20),
            ActionCandidate("withdraw", 0.10),
        ],
        actor_id="jay",
        context="ordinary v0.1 decision",
    )
    engine.chat("jay", "Are you still thinking about the workshop?")

    status = engine.status()
    with engine.store.connect() as conn:
        table_counts = {
            "memories": conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0],
            "beliefs": conn.execute("SELECT COUNT(*) FROM beliefs").fetchone()[0],
            "commitments": conn.execute("SELECT COUNT(*) FROM commitments").fetchone()[0],
            "expectations": conn.execute("SELECT COUNT(*) FROM expectations").fetchone()[0],
            "goals": conn.execute("SELECT COUNT(*) FROM goals").fetchone()[0],
            "concerns": conn.execute("SELECT COUNT(*) FROM concerns").fetchone()[0],
        }
        schema_version = int(
            conn.execute(
                "SELECT value FROM meta WHERE key='schema_version'"
            ).fetchone()[0]
        )

    canonical = engine.store.iter_events(canonical_only=True)
    manifest = {
        "source": "Azimn/Frankenstein@fdaf5be89ccf6991a20eb54649d5318a9adcb6ff",
        "schema_version": schema_version,
        "origin_digest": engine.origin.digest(),
        "projection_digest": engine.store.projection_digest(),
        "max_event_seq": engine.store.max_seq(),
        "canonical_event_ids": [event.event_id for event in canonical],
        "canonical_event_hashes": [event.event_hash for event in canonical],
        "table_counts": table_counts,
        "status": status,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    create_backup(engine, backup)


if __name__ == "__main__":
    main()
