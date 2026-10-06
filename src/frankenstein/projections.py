from __future__ import annotations

from typing import Any
import json
import re

from .storage import SQLiteStore
from .types import Canonicality, EventKind, EventRecord, new_id


def _clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(value)))


class ProjectionManager:
    def __init__(self, store: SQLiteStore, origin):
        self.store = store
        self.origin = origin

    def ensure_current(self) -> None:
        with self.store.connect() as conn:
            need_count = int(conn.execute("SELECT COUNT(*) FROM needs").fetchone()[0])
        if self.store.projection_cursor() != self.store.max_seq() or need_count == 0:
            self.rebuild()

    def rebuild(self) -> None:
        with self.store.transaction() as conn:
            for table in ("needs", "affect", "relationships", "beliefs", "commitments", "expectations", "goals", "concerns", "habits", "memories", "memory_terms", "memory_edges", "runtime_state"):
                conn.execute(f"DELETE FROM {table}")
            for name, value in self.origin.baseline_needs.items():
                conn.execute("INSERT INTO needs(name,value,source_event_id) VALUES(?,?,?)", (name, float(value), "origin"))
            for axis in ("valence", "arousal", "tension"):
                conn.execute("INSERT INTO affect(axis,value,source_event_id) VALUES(?,?,?)", (axis, 0.0, "origin"))
            last_seq = 0
            for event in self.store.iter_events(canonical_only=True):
                self._apply(conn, event)
                last_seq = event.seq
            self.store.set_projection_cursor(self.store.max_seq(), conn)

    def apply_event(self, event: EventRecord) -> None:
        if event.canonicality != Canonicality.CANONICAL.value:
            self.store.set_projection_cursor(event.seq)
            return
        with self.store.transaction() as conn:
            self._apply(conn, event)
            self.store.set_projection_cursor(event.seq, conn)

    def _apply(self, conn, event: EventRecord) -> None:
        p = event.payload
        kind = event.kind
        if kind == EventKind.NEED_UPDATE.value:
            name = str(p["name"])
            if "value" in p:
                value = _clamp(float(p["value"]), 0.0, 1.0)
            else:
                row = conn.execute("SELECT value FROM needs WHERE name=?", (name,)).fetchone()
                base = float(row[0]) if row else float(self.origin.baseline_needs.get(name, 0.5))
                value = _clamp(base + float(p.get("delta", 0.0)), 0.0, 1.0)
            conn.execute("INSERT INTO needs(name,value,source_event_id) VALUES(?,?,?) ON CONFLICT(name) DO UPDATE SET value=excluded.value,source_event_id=excluded.source_event_id", (name, value, event.event_id))
        elif kind == EventKind.AFFECT_UPDATE.value:
            for axis, delta in dict(p.get("deltas", {})).items():
                if axis not in {"valence", "arousal", "tension"}:
                    continue
                row = conn.execute("SELECT value FROM affect WHERE axis=?", (axis,)).fetchone()
                base = float(row[0]) if row else 0.0
                value = _clamp(base + float(delta))
                conn.execute("INSERT INTO affect(axis,value,source_event_id) VALUES(?,?,?) ON CONFLICT(axis) DO UPDATE SET value=excluded.value,source_event_id=excluded.source_event_id", (axis, value, event.event_id))
        elif kind == EventKind.RELATIONSHIP_UPDATE.value:
            actor = str(p["actor_id"])
            for dim, delta in dict(p.get("deltas", {})).items():
                row = conn.execute("SELECT value FROM relationships WHERE actor_id=? AND dimension=?", (actor, dim)).fetchone()
                base = float(row[0]) if row else float(self.origin.relationship_defaults.get(dim, 0.0))
                value = _clamp(base + float(delta))
                conn.execute("INSERT INTO relationships(actor_id,dimension,value,source_event_id) VALUES(?,?,?,?) ON CONFLICT(actor_id,dimension) DO UPDATE SET value=excluded.value,source_event_id=excluded.source_event_id", (actor, dim, value, event.event_id))
        elif kind == EventKind.BELIEF_UPDATE.value:
            belief_id = str(p.get("belief_id") or new_id())
            conn.execute("INSERT INTO beliefs(belief_id,subject,predicate,object_json,confidence,status,evidence_json,source_event_id) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(belief_id) DO UPDATE SET subject=excluded.subject,predicate=excluded.predicate,object_json=excluded.object_json,confidence=excluded.confidence,status=excluded.status,evidence_json=excluded.evidence_json,source_event_id=excluded.source_event_id",
                         (belief_id, str(p["subject"]), str(p["predicate"]), json.dumps(p.get("object"), sort_keys=True), _clamp(float(p.get("confidence", 0.5)), 0.0, 1.0), str(p.get("status", "active")), json.dumps(list(p.get("evidence", []))), event.event_id))
        elif kind == EventKind.COMMITMENT_CREATED.value:
            conn.execute("INSERT OR REPLACE INTO commitments(commitment_id,description,actor_id,due_at,status,source_event_id) VALUES(?,?,?,?,?,?)", (str(p["commitment_id"]), str(p["description"]), p.get("actor_id"), p.get("due_at"), "open", event.event_id))
        elif kind == EventKind.COMMITMENT_UPDATED.value:
            conn.execute("UPDATE commitments SET status=?,source_event_id=? WHERE commitment_id=?", (str(p["status"]), event.event_id, str(p["commitment_id"])))
        elif kind == EventKind.EXPECTATION_CREATED.value:
            conn.execute("INSERT OR REPLACE INTO expectations(expectation_id,description,actor_id,confidence,status,due_at,source_event_id) VALUES(?,?,?,?,?,?,?)", (str(p["expectation_id"]), str(p["description"]), p.get("actor_id"), _clamp(float(p.get("confidence", 0.5)), 0.0, 1.0), "open", p.get("due_at"), event.event_id))
        elif kind == EventKind.EXPECTATION_UPDATED.value:
            conn.execute("UPDATE expectations SET status=?,source_event_id=? WHERE expectation_id=?", (str(p["status"]), event.event_id, str(p["expectation_id"])))
        elif kind == EventKind.GOAL_CREATED.value:
            conn.execute("INSERT OR REPLACE INTO goals(goal_id,description,priority,status,parent_goal_id,source_event_id) VALUES(?,?,?,?,?,?)", (str(p["goal_id"]), str(p["description"]), _clamp(float(p.get("priority", 0.5)), 0.0, 1.0), "active", p.get("parent_goal_id"), event.event_id))
        elif kind == EventKind.GOAL_UPDATED.value:
            conn.execute("UPDATE goals SET status=?,source_event_id=? WHERE goal_id=?", (str(p["status"]), event.event_id, str(p["goal_id"])))
        elif kind == EventKind.CONCERN_UPDATE.value:
            cid = str(p.get("concern_id") or new_id())
            conn.execute("INSERT INTO concerns(concern_id,description,intensity,status,source_event_id) VALUES(?,?,?,?,?) ON CONFLICT(concern_id) DO UPDATE SET description=excluded.description,intensity=excluded.intensity,status=excluded.status,source_event_id=excluded.source_event_id", (cid, str(p["description"]), _clamp(float(p.get("intensity", 0.5)), 0.0, 1.0), str(p.get("status", "active")), event.event_id))
        elif kind in (EventKind.MEMORY_FORMED.value, EventKind.REFLECTION_NOTE.value, EventKind.CONSOLIDATION_SUMMARY.value):
            mid = str(p.get("memory_id") or new_id())
            tags = tuple(str(x) for x in p.get("tags", ()))
            conn.execute("INSERT OR REPLACE INTO memories(memory_id,kind,actor_id,text,tags_json,salience,valence,arousal,created_at,source_event_id) VALUES(?,?,?,?,?,?,?,?,?,?)", (mid, str(p.get("memory_kind", kind)), p.get("actor_id"), str(p["text"]), json.dumps(tags), _clamp(float(p.get("salience", 0.5)), 0.0, 1.0), _clamp(float(p.get("valence", 0.0))), _clamp(float(p.get("arousal", 0.0))), event.created_at, event.event_id))
            self._link_memory(conn, mid, p.get("actor_id"), tags)
        elif kind == EventKind.ACTION_OUTCOME.value:
            action = p.get("action_name")
            if action:
                row = conn.execute("SELECT value,count FROM habits WHERE action_name=?", (action,)).fetchone()
                old, count = (float(row[0]), int(row[1])) if row else (0.0, 0)
                reward = _clamp(float(p.get("reward", 0.0)))
                new_value = _clamp(old + 0.2 * (reward - old))
                conn.execute("INSERT INTO habits(action_name,value,count,source_event_id) VALUES(?,?,?,?) ON CONFLICT(action_name) DO UPDATE SET value=excluded.value,count=excluded.count,source_event_id=excluded.source_event_id", (str(action), new_value, count + 1, event.event_id))
        elif kind == EventKind.SUBJECT_ACTION.value:
            conn.execute("INSERT INTO runtime_state(key,value_json,source_event_id) VALUES('last_action',?,?) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,source_event_id=excluded.source_event_id", (json.dumps(p, sort_keys=True), event.event_id))

    def _link_memory(self, conn, memory_id: str, actor_id: str | None, tags: tuple[str, ...]) -> None:
        current = conn.execute("SELECT text FROM memories WHERE memory_id=?", (memory_id,)).fetchone()
        terms = set(re.findall(r"[a-z0-9']+", ((current["text"] if current else "") + " " + " ".join(tags)).lower()))
        conn.executemany("INSERT OR IGNORE INTO memory_terms(term,memory_id) VALUES(?,?)", [(term, memory_id) for term in sorted(terms)])

        rows = conn.execute("SELECT memory_id,actor_id,tags_json FROM memories WHERE memory_id<>? ORDER BY created_at DESC LIMIT 80", (memory_id,)).fetchall()
        tagset = set(tags)
        candidates: list[tuple[float, str, str]] = []
        for row in rows:
            other_tags = set(json.loads(row["tags_json"]))
            weight = 0.0
            reasons: list[str] = []
            if actor_id and row["actor_id"] == actor_id:
                weight += 0.35
                reasons.append("same_actor")
            overlap = len(tagset & other_tags)
            if overlap:
                weight += min(0.5, overlap * 0.15)
                reasons.append("shared_tags")
            if weight > 0:
                candidates.append((weight, row["memory_id"], "+".join(reasons)))
        for weight, target, reason in sorted(candidates, key=lambda x: (-x[0], x[1]))[:12]:
            conn.execute("INSERT OR REPLACE INTO memory_edges(source_id,target_id,weight,reason) VALUES(?,?,?,?)", (memory_id, target, weight, reason))
            conn.execute("INSERT OR REPLACE INTO memory_edges(source_id,target_id,weight,reason) VALUES(?,?,?,?)", (target, memory_id, weight, reason))
