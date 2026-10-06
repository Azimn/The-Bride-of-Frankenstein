from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
import hashlib
import json

from .types import stable_json


@dataclass(frozen=True)
class CharacterOrigin:
    entity_id: str
    display_name: str
    version: int = 1
    description: str = ""
    traits: dict[str, float] = field(default_factory=dict)
    values: dict[str, float] = field(default_factory=dict)
    voice: tuple[str, ...] = ()
    baseline_needs: dict[str, float] = field(default_factory=lambda: {
        "energy": 0.7,
        "safety": 0.7,
        "affiliation": 0.5,
        "competence": 0.5,
        "curiosity": 0.5,
    })
    relationship_defaults: dict[str, float] = field(default_factory=lambda: {
        "trust": 0.0,
        "familiarity": 0.0,
        "attachment": 0.0,
        "respect": 0.0,
        "obligation": 0.0,
        "resentment": 0.0,
        "fear": 0.0,
    })
    action_priors: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.entity_id.strip():
            raise ValueError("entity_id is required")
        if not self.display_name.strip():
            raise ValueError("display_name is required")
        if self.version < 1:
            raise ValueError("version must be positive")
        for section_name, section in (("traits", self.traits), ("values", self.values), ("baseline_needs", self.baseline_needs), ("relationship_defaults", self.relationship_defaults)):
            for key, value in section.items():
                if not isinstance(key, str) or not key:
                    raise ValueError(f"{section_name} keys must be non-empty strings")
                if not isinstance(value, (int, float)):
                    raise ValueError(f"{section_name}.{key} must be numeric")
                if not -1.0 <= float(value) <= 1.0:
                    raise ValueError(f"{section_name}.{key} must be between -1 and 1")

    def digest(self) -> str:
        self.validate()
        return hashlib.sha256(stable_json(asdict(self)).encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "CharacterOrigin":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        data["voice"] = tuple(data.get("voice", ()))
        origin = cls(**data)
        origin.validate()
        return origin
