from __future__ import annotations

from dataclasses import dataclass

from bride.contracts import MechanismSpec, QualificationCase
from bride.registry import DONOR_BY_ID


@dataclass(frozen=True)
class StaticIntervention:
    spec: MechanismSpec
    payload: dict

    def intervention_payload(self, case: QualificationCase, replicate: int) -> dict:
        return dict(self.payload)


def donor(mechanism_id: str, **payload) -> StaticIntervention:
    return StaticIntervention(DONOR_BY_ID[mechanism_id], payload)
