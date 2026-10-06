from __future__ import annotations

import pytest

from frankenstein.cartridge import CharacterOrigin
from frankenstein.engine import FrankensteinEngine


@pytest.fixture
def origin():
    return CharacterOrigin(
        entity_id="test-character",
        display_name="Mara",
        traits={"curiosity": 0.5, "caution": 0.2},
        values={"honesty": 0.8},
        voice=("Use direct language.",),
        action_priors={"engage": 0.03},
    )


@pytest.fixture
def engine(tmp_path, origin):
    return FrankensteinEngine(tmp_path / "home", origin)
