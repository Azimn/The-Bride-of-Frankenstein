from __future__ import annotations

from dataclasses import dataclass

from .engine import FrankensteinEngine


@dataclass(frozen=True)
class DoctorReport:
    ok: bool
    checks: dict[str, bool]
    details: dict[str, str]


def run_doctor(engine: FrankensteinEngine) -> DoctorReport:
    checks: dict[str, bool] = {}
    details: dict[str, str] = {}
    integrity = engine.store.verify_integrity()
    checks["event_ledger"] = integrity.ok
    details["event_ledger"] = f"{integrity.checked_events} events checked" if integrity.ok else "; ".join(integrity.errors)
    origin_ok = engine.store.get_meta("origin_digest") == engine.origin.digest()
    checks["origin_digest"] = origin_ok
    details["origin_digest"] = "sealed origin matches stored digest" if origin_ok else "sealed origin digest mismatch"
    cursor_ok = engine.store.projection_cursor() == engine.store.max_seq()
    checks["projection_cursor"] = cursor_ok
    details["projection_cursor"] = f"cursor={engine.store.projection_cursor()} max_seq={engine.store.max_seq()}"
    with engine.store.connect() as conn:
        quick = str(conn.execute("PRAGMA quick_check").fetchone()[0])
    checks["sqlite_quick_check"] = quick == "ok"
    details["sqlite_quick_check"] = quick
    return DoctorReport(all(checks.values()), checks, details)
