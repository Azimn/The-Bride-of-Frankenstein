from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import re
from typing import Protocol

from .storage import SQLiteStore
from .types import utc_now


_TOKEN = re.compile(r"[a-z0-9']+")


class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> list[float]: ...


@dataclass(frozen=True)
class MemoryHit:
    memory_id: str
    text: str
    actor_id: str | None
    score: float
    salience: float
    source_event_id: str


class MemoryIndex:
    def __init__(self, store: SQLiteStore, embedding_provider: EmbeddingProvider | None = None):
        self.store = store
        self.embedding_provider = embedding_provider

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return set(_TOKEN.findall(text.lower()))

    @staticmethod
    def _recency(created_at: str) -> float:
        try:
            dt = datetime.fromisoformat(created_at)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            days = max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0)
            return math.exp(-days / 30.0)
        except Exception:
            return 0.0

    def search(self, query: str, *, actor_id: str | None = None, top_k: int = 8, exclude: set[str] | None = None) -> list[MemoryHit]:
        exclude = exclude or set()
        q = self._tokens(query)
        with self.store.connect() as conn:
            candidate_ids: set[str] = set()
            if q:
                placeholders = ",".join("?" for _ in q)
                for row in conn.execute(f"SELECT DISTINCT memory_id FROM memory_terms WHERE term IN ({placeholders}) LIMIT 800", tuple(sorted(q))):
                    candidate_ids.add(str(row["memory_id"]))
            for row in conn.execute("SELECT memory_id FROM memories ORDER BY created_at DESC LIMIT 80"):
                candidate_ids.add(str(row["memory_id"]))
            if actor_id:
                for row in conn.execute("SELECT memory_id FROM memories WHERE actor_id=? ORDER BY created_at DESC LIMIT 80", (actor_id,)):
                    candidate_ids.add(str(row["memory_id"]))
            if candidate_ids:
                placeholders = ",".join("?" for _ in candidate_ids)
                rows = conn.execute(f"SELECT * FROM memories WHERE memory_id IN ({placeholders})", tuple(candidate_ids)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM memories ORDER BY created_at DESC LIMIT 80").fetchall()
        scored: dict[str, tuple[float, object]] = {}
        for row in rows:
            if row["memory_id"] in exclude:
                continue
            tokens = self._tokens(row["text"] + " " + " ".join(json.loads(row["tags_json"])))
            lexical = len(q & tokens) / max(1.0, math.sqrt(len(q) * max(1, len(tokens)))) if q else 0.0
            actor_bonus = 0.15 if actor_id and row["actor_id"] == actor_id else 0.0
            score = 0.55 * lexical + 0.20 * float(row["salience"]) + 0.10 * self._recency(row["created_at"]) + actor_bonus
            scored[row["memory_id"]] = (score, row)
        seeds = sorted(scored.items(), key=lambda kv: kv[1][0], reverse=True)[: max(top_k, 4)]
        seed_scores = {mid: score for mid, (score, _) in seeds}
        if seed_scores:
            with self.store.connect() as conn:
                placeholders = ",".join("?" for _ in seed_scores)
                edges = conn.execute(f"SELECT source_id,target_id,weight FROM memory_edges WHERE source_id IN ({placeholders})", tuple(seed_scores)).fetchall()
            linked_ids = {str(edge["target_id"]) for edge in edges if str(edge["target_id"]) not in scored}
            if linked_ids:
                with self.store.connect() as conn:
                    placeholders = ",".join("?" for _ in linked_ids)
                    linked_rows = conn.execute(f"SELECT * FROM memories WHERE memory_id IN ({placeholders})", tuple(linked_ids)).fetchall()
                for row in linked_rows:
                    if row["memory_id"] not in exclude:
                        scored[row["memory_id"]] = (0.0, row)
            for edge in edges:
                if edge["source_id"] in seed_scores and edge["target_id"] in scored:
                    base, row = scored[edge["target_id"]]
                    scored[edge["target_id"]] = (base + 0.20 * seed_scores[edge["source_id"]] * float(edge["weight"]), row)
        ordered = sorted(scored.values(), key=lambda x: x[0], reverse=True)
        selected: list[MemoryHit] = []
        selected_tokens: list[set[str]] = []
        for score, row in ordered:
            tokens = self._tokens(row["text"])
            redundancy = max((len(tokens & s) / max(1, len(tokens | s)) for s in selected_tokens), default=0.0)
            mmr = 0.8 * score - 0.2 * redundancy
            hit = MemoryHit(row["memory_id"], row["text"], row["actor_id"], float(mmr), float(row["salience"]), row["source_event_id"])
            selected.append(hit)
            selected_tokens.append(tokens)
            if len(selected) >= top_k:
                break
        if selected:
            with self.store.transaction() as conn:
                now = utc_now()
                conn.executemany("UPDATE memories SET access_count=access_count+1,last_accessed=? WHERE memory_id=?", [(now, h.memory_id) for h in selected])
        return selected
