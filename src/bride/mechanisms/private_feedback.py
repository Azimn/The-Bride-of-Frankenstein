from __future__ import annotations


class PrivateThoughtFeedback:
    """Jelly-Psiduck-inspired bounded admission path."""

    def admit(self, engine, text: str, *, intensity: float = 0.45):
        proposal = engine.private_thought(text)
        reflection = engine.admit_reflection(proposal.event_id, text)
        concern_id = engine.set_concern(
            text,
            intensity=max(0.0, min(0.65, float(intensity))),
            cause_ids=(reflection.event_id,),
        )
        return proposal.event_id, reflection.event_id, concern_id
