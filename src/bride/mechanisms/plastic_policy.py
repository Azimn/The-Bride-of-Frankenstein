from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ContextualPlasticPolicy:
    """Small interpretable challenger for recurrent/plastic policy claims."""

    learning_rate: float = 0.25
    values: dict[tuple[str, str], float] = field(default_factory=dict)

    def score(self, context: str, action: str) -> float:
        return float(self.values.get((context, action), 0.0))

    def choose(self, context: str, actions: tuple[str, ...]) -> str:
        if not actions:
            raise ValueError("actions required")
        return max(actions, key=lambda a: (self.score(context, a), -actions.index(a)))

    def learn(self, context: str, action: str, reward: float) -> None:
        key = (context, action)
        old = self.values.get(key, 0.0)
        reward = max(-1.0, min(1.0, float(reward)))
        self.values[key] = old + self.learning_rate * (reward - old)
