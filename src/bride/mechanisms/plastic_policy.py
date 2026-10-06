from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path


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

    def to_dict(self) -> dict:
        return {
            "learning_rate": self.learning_rate,
            "values": [
                {"context": context, "action": action, "value": value}
                for (context, action), value in sorted(self.values.items())
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContextualPlasticPolicy":
        policy = cls(learning_rate=float(data.get("learning_rate", 0.25)))
        for row in data.get("values", ()):
            policy.values[(str(row["context"]), str(row["action"]))] = float(row["value"])
        return policy

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "ContextualPlasticPolicy":
        target = Path(path)
        if not target.exists():
            return cls()
        return cls.from_dict(json.loads(target.read_text(encoding="utf-8")))
