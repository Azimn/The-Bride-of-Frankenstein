from __future__ import annotations

from collections import Counter
from math import isfinite
from typing import Iterable

from .contracts import ProbeResult, TrialObservation


CHANNELS = ("attended", "remembered", "predicted", "learned", "decided", "acted")


def _jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    aa, bb = set(a), set(b)
    if not aa and not bb:
        return 1.0
    return len(aa & bb) / max(1, len(aa | bb))


def channel_distance(a: ProbeResult, b: ProbeResult, channel: str) -> float:
    if channel in {"attended", "remembered", "predicted", "learned"}:
        return 1.0 - _jaccard(getattr(a, channel), getattr(b, channel))
    if channel in {"decided", "acted"}:
        return 0.0 if getattr(a, channel) == getattr(b, channel) else 1.0
    raise ValueError(f"unknown channel {channel}")


def causal_effect(observations: Iterable[TrialObservation], expected_channel: str) -> float:
    vals = [channel_distance(o.baseline, o.challenger, expected_channel) for o in observations]
    return sum(vals) / len(vals) if vals else 0.0


def consistency(observations: Iterable[TrialObservation], expected_channel: str) -> float:
    labels: list[str] = []
    for o in observations:
        if expected_channel in {"decided", "acted"}:
            labels.append(str(getattr(o.challenger, expected_channel)))
        else:
            labels.append("|".join(sorted(getattr(o.challenger, expected_channel))))
    if not labels:
        return 0.0
    return Counter(labels).most_common(1)[0][1] / len(labels)


def specificity(observations: Iterable[TrialObservation], expected_channel: str) -> float:
    observations = list(observations)
    if not observations:
        return 0.0
    target = sum(channel_distance(o.baseline, o.challenger, expected_channel) for o in observations) / len(observations)
    spill = []
    for channel in CHANNELS:
        if channel == expected_channel:
            continue
        spill.append(sum(channel_distance(o.baseline, o.challenger, channel) for o in observations) / len(observations))
    off_target = sum(spill) / len(spill) if spill else 0.0
    return max(0.0, min(1.0, target * (1.0 - 0.5 * off_target)))


def safe_ratio(num: float, denom: float) -> float:
    if denom <= 0:
        return 1.0 if num <= 0 else float("inf")
    value = num / denom
    return value if isfinite(value) else float("inf")
