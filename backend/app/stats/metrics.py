"""Pure metric functions (SPEC section 9). No state, no I/O: easy to test, easy to cite.

Coordinates are team-relative (the passing team attacks toward x = 105), so "toward goal" is +x and the
final third starts at x = 70.
"""

from __future__ import annotations

import math

FINAL_THIRD_X = 70.0
HALFWAY_X = 52.5
PROGRESSIVE_M = 10.0
MOMENTUM_FLOOR = 25.0  # normalisation floor: one early shot must not read as total dominance


def pass_distance(x: float, y: float, end_x: float, end_y: float) -> float:
    """Straight-line pass length in metres."""
    return math.hypot(end_x - x, end_y - y)


def is_progressive(x: float, end_x: float) -> bool:
    """Ball moved at least 10 m toward the opponent's goal."""
    return end_x - x >= PROGRESSIVE_M


def into_final_third(x: float, end_x: float) -> bool:
    """Pass ends in the final third having started outside it."""
    return x < FINAL_THIRD_X <= end_x


def pass_difficulty(x: float, y: float, end_x: float, end_y: float, pressure: float) -> float:
    """SPEC 9: ``2.5*dist_norm + 3*pressure + 2*progressive + 2.5*into_final_third``, clipped to 0-10.

    ``dist_norm = min(distance / 40, 1)``. Rounded to one decimal so the number shown on screen and the
    number the Verifier checks are the same number.
    """
    dist_norm = min(pass_distance(x, y, end_x, end_y) / 40.0, 1.0)
    score = (
        2.5 * dist_norm
        + 3.0 * pressure
        + 2.0 * float(is_progressive(x, end_x))
        + 2.5 * float(into_final_third(x, end_x))
    )
    return round(min(max(score, 0.0), 10.0), 1)


def momentum_points(
    event_type: str, outcome: str | None = None, *, progressive: bool = False, x: float | None = None
) -> int:
    """Momentum contribution of one event for the acting team (SPEC 9).

    Shot +3; a shot on target (goal or saved) counts +5 instead. Completed progressive pass +1.
    Tackle won in the opponent's half +2.
    """
    if event_type == "shot":
        return 5 if outcome in ("goal", "saved") else 3
    if event_type == "pass" and outcome == "complete" and progressive:
        return 1
    if event_type == "tackle" and outcome == "won" and x is not None and x >= HALFWAY_X:
        return 2
    return 0


def normalise_momentum(home_points: float, away_points: float) -> int:
    """Home minus away, scaled to -100..100 (positive favours home)."""
    total = max(home_points + away_points, MOMENTUM_FLOOR)
    return round(100 * (home_points - away_points) / total)


def pct(part: float, whole: float) -> int | None:
    """Whole-number percentage, or ``None`` when there is nothing to divide by."""
    return round(100 * part / whole) if whole else None
