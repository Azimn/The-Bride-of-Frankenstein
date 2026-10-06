"""The Bride of Frankenstein donor qualification laboratory."""

from .contracts import (
    DonorRole,
    MechanismSpec,
    QualificationCase,
    QualificationResult,
    PromotionVerdict,
)
from .qualification import QualificationHarness
from .registry import DONORS

__all__ = [
    "DONORS",
    "DonorRole",
    "MechanismSpec",
    "PromotionVerdict",
    "QualificationCase",
    "QualificationHarness",
    "QualificationResult",
]

__version__ = "0.2.0-lab"
