from __future__ import annotations

from pathlib import Path
import hashlib
import json
import shutil
import tarfile
import tempfile

from .engine import FrankensteinEngine
from .cartridge import CharacterOrigin
from .storage import SQLiteStore


def create_backup(engine: FrankensteinEngine, target: str | Path) -> Path:
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        db = engine.store.backup_to(root / "state.sqlite3")
        shutil.copy2(engine.origin_path, root / "character.origin.json")
        manifest = {
            "origin_digest": engine.origin.digest(),
            "projection_digest": engine.store.projection_digest(),
            "event_count": engine.store.max_seq(),
        }
        (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with tarfile.open(target, "w:gz") as tf:
            for name in ("state.sqlite3", "character.origin.json", "manifest.json"):
                tf.add(root / name, arcname=name)
    return target


def restore_backup(archive: str | Path, destination: str | Path, *, force: bool = False) -> FrankensteinEngine:
    archive = Path(archive)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    if not force and ((destination / "state.sqlite3").exists() or (destination / "character.origin.json").exists()):
        raise FileExistsError("restore destination already contains character state; choose an empty directory")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        with tarfile.open(archive, "r:gz") as tf:
            safe_names = {"state.sqlite3", "character.origin.json", "manifest.json"}
            names = set(tf.getnames())
            if names != safe_names:
                raise ValueError("backup contains unexpected or missing files")
            for name in sorted(safe_names):
                member = tf.getmember(name)
                if not member.isfile() or member.name != name:
                    raise ValueError("backup contains an unsafe member")
                src = tf.extractfile(member)
                if src is None:
                    raise ValueError("backup member could not be read")
                (root / name).write_bytes(src.read())
        origin = CharacterOrigin.load(root / "character.origin.json")
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        if origin.digest() != manifest["origin_digest"]:
            raise ValueError("backup origin digest mismatch")
        probe = SQLiteStore(root / "state.sqlite3")
        report = probe.verify_integrity()
        if not report.ok:
            raise ValueError("backup event ledger failed integrity verification")
        shutil.copy2(root / "state.sqlite3", destination / "state.sqlite3")
        shutil.copy2(root / "character.origin.json", destination / "character.origin.json")
    engine = FrankensteinEngine.open(destination)
    if engine.origin.digest() != manifest["origin_digest"]:
        raise ValueError("restored origin digest mismatch")
    engine.projections.rebuild()
    return engine
