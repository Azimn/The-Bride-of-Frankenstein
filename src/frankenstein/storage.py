from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
import hashlib
import json
import shutil
import sqlite3

from .types import Authority, Canonicality, EventKind, EventRecord, IntegrityReport, new_id, stable_json, utc_now


SCHEMA_VERSION = 1


_SCHEMA = r"""
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    kind TEXT NOT NULL,
    authority TEXT NOT NULL,
    canonicality TEXT NOT NULL,
    actor_id TEXT,
    payload_json TEXT NOT NULL,
    cause_ids_json TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    event_hash TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_events_kind ON events(kind);
CREATE INDEX IF NOT EXISTS idx_events_actor ON events(actor_id);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);

CREATE TABLE IF NOT EXISTS needs (
    name TEXT PRIMARY KEY,
    value REAL NOT NULL,
    source_event_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS affect (
    axis TEXT PRIMARY KEY,
    value REAL NOT NULL,
    source_event_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS relationships (
    actor_id TEXT NOT NULL,
    dimension TEXT NOT NULL,
    value REAL NOT NULL,
    source_event_id TEXT NOT NULL,
    PRIMARY KEY(actor_id, dimension)
);
CREATE TABLE IF NOT EXISTS beliefs (
    belief_id TEXT PRIMARY KEY,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object_json TEXT NOT NULL,
    confidence REAL NOT NULL,
    status TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    source_event_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS commitments (
    commitment_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    actor_id TEXT,
    due_at TEXT,
    status TEXT NOT NULL,
    source_event_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS expectations (
    expectation_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    actor_id TEXT,
    confidence REAL NOT NULL,
    status TEXT NOT NULL,
    due_at TEXT,
    source_event_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS goals (
    goal_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    priority REAL NOT NULL,
    status TEXT NOT NULL,
    parent_goal_id TEXT,
    source_event_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS concerns (
    concern_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    intensity REAL NOT NULL,
    status TEXT NOT NULL,
    source_event_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS habits (
    action_name TEXT PRIMARY KEY,
    value REAL NOT NULL,
    count INTEGER NOT NULL,
    source_event_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS memories (
    memory_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    actor_id TEXT,
    text TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    salience REAL NOT NULL,
    valence REAL NOT NULL,
    arousal REAL NOT NULL,
    created_at TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    access_count INTEGER NOT NULL DEFAULT 0,
    last_accessed TEXT
);
CREATE INDEX IF NOT EXISTS idx_memories_actor ON memories(actor_id);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
CREATE TABLE IF NOT EXISTS memory_terms (
    term TEXT NOT NULL,
    memory_id TEXT NOT NULL,
    PRIMARY KEY(term, memory_id)
);
CREATE INDEX IF NOT EXISTS idx_memory_terms_memory ON memory_terms(memory_id);
CREATE TABLE IF NOT EXISTS memory_edges (
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    weight REAL NOT NULL,
    reason TEXT NOT NULL,
    PRIMARY KEY(source_id, target_id)
);
CREATE TABLE IF NOT EXISTS runtime_state (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    source_event_id TEXT NOT NULL
);
"""


_ALLOWED_CANONICAL_AUTHORITIES: dict[str, set[str]] = {
    EventKind.WORLD_EVENT.value: {Authority.HOST.value, Authority.SYSTEM.value},
    EventKind.SOCIAL_OBSERVATION.value: {Authority.HOST.value},
    EventKind.SUBJECT_ACTION.value: {Authority.SUBJECT.value},
    EventKind.ACTION_OUTCOME.value: {Authority.HOST.value},
    EventKind.RELATIONSHIP_UPDATE.value: {Authority.SUBJECT.value, Authority.SYSTEM.value},
    EventKind.NEED_UPDATE.value: {Authority.SYSTEM.value, Authority.SUBJECT.value},
    EventKind.BELIEF_UPDATE.value: {Authority.SUBJECT.value},
    EventKind.COMMITMENT_CREATED.value: {Authority.SUBJECT.value},
    EventKind.COMMITMENT_UPDATED.value: {Authority.SUBJECT.value, Authority.SYSTEM.value},
    EventKind.GOAL_CREATED.value: {Authority.SUBJECT.value},
    EventKind.GOAL_UPDATED.value: {Authority.SUBJECT.value, Authority.SYSTEM.value},
    EventKind.CONCERN_UPDATE.value: {Authority.SUBJECT.value, Authority.SYSTEM.value},
    EventKind.MEMORY_FORMED.value: {Authority.SUBJECT.value, Authority.SYSTEM.value},
    EventKind.REFLECTION_NOTE.value: {Authority.SUBJECT.value},
    EventKind.CONSOLIDATION_SUMMARY.value: {Authority.SUBJECT.value},
    EventKind.CHECKPOINT.value: {Authority.SYSTEM.value},
    EventKind.DECISION_RECEIPT.value: {Authority.SYSTEM.value},
    EventKind.INTERPRETATION.value: {Authority.SUBJECT.value},
    EventKind.AFFECT_UPDATE.value: {Authority.SYSTEM.value, Authority.SUBJECT.value},
    EventKind.EXPECTATION_CREATED.value: {Authority.SUBJECT.value},
    EventKind.EXPECTATION_UPDATED.value: {Authority.SUBJECT.value, Authority.SYSTEM.value},
}


class _ClosingConnection(sqlite3.Connection):
    """SQLite connection whose context manager also releases the file handle.

    sqlite3.Connection.__exit__ commits or rolls back but deliberately does not
    close the connection. That is easy to miss on POSIX, where an open database
    file may still be unlinked, and becomes a correctness bug on Windows.
    Frankenstein treats the end of a ``with store.connect()`` block as the end
    of ownership, so the connection must close there.
    """

    def __exit__(self, exc_type, exc, tb):
        try:
            return super().__exit__(exc_type, exc, tb)
        finally:
            self.close()


class SQLiteStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(_SCHEMA)
            conn.execute("INSERT OR IGNORE INTO meta(key,value) VALUES('schema_version',?)", (str(SCHEMA_VERSION),))
            stored = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0]
            if int(stored) != SCHEMA_VERSION:
                raise RuntimeError(f"unsupported database schema version {stored}; runtime supports {SCHEMA_VERSION}")
            conn.execute("INSERT OR IGNORE INTO meta(key,value) VALUES('projection_cursor','0')")

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30, factory=_ClosingConnection)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_meta(self, key: str, default: str | None = None) -> str | None:
        with self.connect() as conn:
            row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def set_meta(self, key: str, value: str) -> None:
        with self.transaction() as conn:
            conn.execute("INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

    def append_event(
        self,
        kind: EventKind | str,
        authority: Authority | str,
        payload: dict[str, Any],
        *,
        actor_id: str | None = None,
        cause_ids: tuple[str, ...] = (),
        canonicality: Canonicality | str = Canonicality.CANONICAL,
        event_id: str | None = None,
        created_at: str | None = None,
    ) -> EventRecord:
        kind_v = kind.value if isinstance(kind, EventKind) else str(kind)
        authority_v = authority.value if isinstance(authority, Authority) else str(authority)
        canon_v = canonicality.value if isinstance(canonicality, Canonicality) else str(canonicality)
        if canon_v == Canonicality.CANONICAL.value:
            allowed = _ALLOWED_CANONICAL_AUTHORITIES.get(kind_v)
            if not allowed or authority_v not in allowed:
                raise ValueError(f"canonical {kind_v} cannot be authored by {authority_v}")
        event_id = event_id or new_id()
        created_at = created_at or utc_now()
        payload_json = stable_json(payload)
        cause_json = stable_json(list(cause_ids))
        with self.transaction() as conn:
            for cause in cause_ids:
                if not conn.execute("SELECT 1 FROM events WHERE event_id=?", (cause,)).fetchone():
                    raise ValueError(f"unknown cause event {cause}")
            prev = conn.execute("SELECT event_hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
            prev_hash = prev[0] if prev else "0" * 64
            material = stable_json({
                "event_id": event_id,
                "created_at": created_at,
                "kind": kind_v,
                "authority": authority_v,
                "canonicality": canon_v,
                "actor_id": actor_id,
                "payload": payload,
                "cause_ids": list(cause_ids),
                "prev_hash": prev_hash,
            })
            event_hash = hashlib.sha256(material.encode("utf-8")).hexdigest()
            cur = conn.execute(
                "INSERT INTO events(event_id,created_at,kind,authority,canonicality,actor_id,payload_json,cause_ids_json,prev_hash,event_hash) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (event_id, created_at, kind_v, authority_v, canon_v, actor_id, payload_json, cause_json, prev_hash, event_hash),
            )
            seq = int(cur.lastrowid)
        return EventRecord(seq, event_id, created_at, kind_v, authority_v, canon_v, actor_id, payload, tuple(cause_ids), prev_hash, event_hash)

    def iter_events(self, *, canonical_only: bool = False, after_seq: int = 0) -> list[EventRecord]:
        query = "SELECT * FROM events WHERE seq>?"
        args: list[Any] = [after_seq]
        if canonical_only:
            query += " AND canonicality=?"
            args.append(Canonicality.CANONICAL.value)
        query += " ORDER BY seq"
        with self.connect() as conn:
            rows = conn.execute(query, args).fetchall()
        return [self._row_to_event(r) for r in rows]

    def event(self, event_id: str) -> EventRecord | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM events WHERE event_id=?", (event_id,)).fetchone()
        return self._row_to_event(row) if row else None

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> EventRecord:
        return EventRecord(
            int(row["seq"]), row["event_id"], row["created_at"], row["kind"], row["authority"], row["canonicality"], row["actor_id"],
            json.loads(row["payload_json"]), tuple(json.loads(row["cause_ids_json"])), row["prev_hash"], row["event_hash"],
        )

    def verify_integrity(self) -> IntegrityReport:
        errors: list[str] = []
        events = self.iter_events()
        expected_prev = "0" * 64
        known: set[str] = set()
        for event in events:
            if event.prev_hash != expected_prev:
                errors.append(f"seq {event.seq}: previous hash mismatch")
            for cause in event.cause_ids:
                if cause not in known:
                    errors.append(f"seq {event.seq}: cause {cause} is not an earlier event")
            material = stable_json({
                "event_id": event.event_id,
                "created_at": event.created_at,
                "kind": event.kind,
                "authority": event.authority,
                "canonicality": event.canonicality,
                "actor_id": event.actor_id,
                "payload": event.payload,
                "cause_ids": list(event.cause_ids),
                "prev_hash": event.prev_hash,
            })
            actual = hashlib.sha256(material.encode("utf-8")).hexdigest()
            if actual != event.event_hash:
                errors.append(f"seq {event.seq}: event hash mismatch")
            expected_prev = event.event_hash
            known.add(event.event_id)
        return IntegrityReport(not errors, len(events), tuple(errors))

    def max_seq(self) -> int:
        with self.connect() as conn:
            return int(conn.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0])

    def projection_cursor(self) -> int:
        return int(self.get_meta("projection_cursor", "0") or 0)

    def set_projection_cursor(self, seq: int, conn: sqlite3.Connection | None = None) -> None:
        if conn is None:
            self.set_meta("projection_cursor", str(seq))
        else:
            conn.execute("INSERT INTO meta(key,value) VALUES('projection_cursor',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(seq),))

    def projection_digest(self) -> str:
        """Digest causal projection state only. Retrieval telemetry is intentionally excluded.

        access_count and last_accessed are cache/observability metadata. They do not currently
        affect decisions, so replay does not need to reproduce them. If that changes, they must
        move behind canonical retrieval events before they are allowed into this digest.
        """
        tables = ["needs", "affect", "relationships", "beliefs", "commitments", "expectations", "goals", "concerns", "habits", "memory_edges", "runtime_state"]
        snapshot: dict[str, Any] = {}
        with self.connect() as conn:
            for table in tables:
                rows = conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
                snapshot[table] = [{k: row[k] for k in row.keys()} for row in rows]
            rows = conn.execute("SELECT memory_id,kind,actor_id,text,tags_json,salience,valence,arousal,created_at,source_event_id FROM memories ORDER BY rowid").fetchall()
            snapshot["memories"] = [{k: row[k] for k in row.keys()} for row in rows]
        return hashlib.sha256(stable_json(snapshot).encode("utf-8")).hexdigest()

    def backup_to(self, target: str | Path) -> Path:
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as src, sqlite3.connect(target, factory=_ClosingConnection) as dst:
            src.backup(dst)
        return target

    def restore_from(self, source: str | Path) -> None:
        source = Path(source)
        probe = SQLiteStore(source)
        report = probe.verify_integrity()
        if not report.ok:
            raise ValueError("backup failed integrity verification: " + "; ".join(report.errors))
        shutil.copy2(source, self.path)
