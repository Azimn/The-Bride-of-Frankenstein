from __future__ import annotations

import io
import json
import sqlite3
import tarfile
import urllib.error
import urllib.request
from threading import Thread

import pytest

from frankenstein.api import APIServer
from frankenstein.backup import create_backup, restore_backup
from frankenstein.doctor import run_doctor
from frankenstein.types import WorldEvent


def test_hash_chain_detects_tampering(engine):
    engine.observe(WorldEvent("A cup breaks."))
    with engine.store.transaction() as conn:
        conn.execute("UPDATE events SET payload_json=? WHERE seq=1", ('{"summary":"forged"}',))
    report = engine.store.verify_integrity()
    assert not report.ok
    assert any("hash mismatch" in x for x in report.errors)


def test_unknown_parent_is_rejected(engine):
    with pytest.raises(ValueError, match="unknown cause"):
        engine.form_memory("Impossible lineage", cause_ids=("missing-event",))


def test_parent_must_precede_child(engine):
    a = engine.observe(WorldEvent("First."))
    b = engine.observe(WorldEvent("Second."))
    assert a.seq < b.seq
    assert engine.store.verify_integrity().ok


def test_backup_restore_round_trip(engine, tmp_path):
    engine.observe(WorldEvent("A clock stops."))
    backup = create_backup(engine, tmp_path / "backup.tgz")
    restored = restore_backup(backup, tmp_path / "restored")
    assert restored.store.verify_integrity().ok
    assert restored.store.projection_digest() == engine.store.projection_digest()


def test_restore_refuses_nonempty_destination(engine, tmp_path):
    backup = create_backup(engine, tmp_path / "backup.tgz")
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "state.sqlite3").write_bytes(b"occupied")
    with pytest.raises(FileExistsError):
        restore_backup(backup, occupied)


def test_restore_rejects_unsafe_archive(tmp_path):
    archive = tmp_path / "unsafe.tgz"
    with tarfile.open(archive, "w:gz") as tf:
        for name, data in {
            "state.sqlite3": b"x",
            "character.origin.json": b"{}",
            "manifest.json": b"{}",
            "../escape": b"bad",
        }.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    with pytest.raises(ValueError, match="unexpected"):
        restore_backup(archive, tmp_path / "dest")


def test_doctor_green_on_healthy_home(engine):
    report = run_doctor(engine)
    assert report.ok
    assert all(report.checks.values())


def test_nonloopback_api_requires_token(engine):
    with pytest.raises(ValueError, match="bearer token"):
        APIServer(engine, host="0.0.0.0", port=0, token=None)


def test_api_auth_and_status(engine):
    server = APIServer(engine, host="127.0.0.1", port=0, token="secret")
    host, port = server.httpd.server_address[:2]
    t = Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        url = f"http://127.0.0.1:{port}/status"
        with pytest.raises(urllib.error.HTTPError) as err:
            urllib.request.urlopen(url, timeout=2)
        assert err.value.code == 401
        req = urllib.request.Request(url, headers={"Authorization": "Bearer secret"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read())
        assert data["integrity_ok"] is True
    finally:
        server.shutdown()
        t.join(timeout=2)


def _writer_process(home: str, prefix: str, count: int):
    from frankenstein.engine import FrankensteinEngine
    from frankenstein.types import WorldEvent
    engine = FrankensteinEngine.open(home)
    for i in range(count):
        engine.observe(WorldEvent(f"{prefix} event {i}", tags=(prefix,)))


def test_cross_process_single_writer_keeps_ledger_valid(tmp_path, origin):
    import multiprocessing as mp
    from frankenstein.engine import FrankensteinEngine
    home = tmp_path / "shared"
    FrankensteinEngine(home, origin)
    ctx = mp.get_context("spawn")
    a = ctx.Process(target=_writer_process, args=(str(home), "a", 8))
    b = ctx.Process(target=_writer_process, args=(str(home), "b", 8))
    a.start(); b.start()
    a.join(20); b.join(20)
    assert a.exitcode == 0
    assert b.exitcode == 0
    reopened = FrankensteinEngine.open(home)
    assert reopened.store.verify_integrity().ok
    assert reopened.store.max_seq() == 32
    assert reopened.store.projection_cursor() == reopened.store.max_seq()


def test_api_event_endpoint(engine):
    server = APIServer(engine, host="127.0.0.1", port=0, token=None)
    port = server.httpd.server_address[1]
    t = Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        body = json.dumps({"summary": "A door opens.", "tags": ["door"], "salience": 0.7}).encode()
        req = urllib.request.Request(f"http://127.0.0.1:{port}/event", data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read())
        assert resp.status == 201
        assert engine.store.event(data["event_id"]) is not None
    finally:
        server.shutdown(); t.join(timeout=2)


def test_store_connection_context_releases_handle(engine):
    """The store context owns and closes its SQLite handle, including on Windows."""
    with engine.store.connect() as conn:
        assert conn.execute("SELECT 1").fetchone()[0] == 1
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")
