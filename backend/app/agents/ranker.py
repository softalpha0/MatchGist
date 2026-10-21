"""Relevance Ranker: how much a moment matters to *this* fan (SPEC section 9.1 adjustments).

Deterministic on purpose: it's arithmetic over the fan profile and the moment, and its reasons are
shown to the fan's System panel row. (SPEC allows a small model call here; rules were enough.)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.fans.profiles import FanProfile
from app.moments.models import Moment

# Which focus metrics a moment type actually moves.
MOVES_METRIC = {
    "xg": {"goal", "big_chance", "half_time", "full_time"},
    "possession": {"momentum_swing", "half_time", "full_time"},
    "momentum": {"momentum_swing", "goal"},
    "pressure": {"pressure_spike"},
    "pass_accuracy": {"elite_pass", "half_time", "full_time"},
    "shot_speed": {"goal", "big_chance"},
}
ANALYST_FAVOURS = {"elite_pass", "pressure_spike", "momentum_swing"}


@dataclass
class Ranking:
    score: int
    involved: bool
    skip: bool = False
    reasons: list[str] = field(default_factory=list)


def involvement(fan: FanProfile, moment: Moment) -> tuple[bool, bool]:
    """(favourite club involved, favourite player involved)."""
    both_teams = moment.type in ("half_time", "full_time")
    club = bool(fan.favorite_club) and (both_teams or moment.team_id == fan.favorite_club)
    player = bool(fan.favorite_player) and (
        moment.player_id == fan.favorite_player or fan.favorite_player in moment.involved_player_ids
    )
    return club, player


def rank(fan: FanProfile, moment: Moment) -> Ranking:
    score = moment.base_score
    reasons = [f"base {moment.base_score} ({moment.type})"]
    club, player = involvement(fan, moment)
    if club:
        score += 30
        reasons.append(f"+30 {fan.favorite_club} involved")
    if player:
        score += 40
        reasons.append("+40 favourite player involved")
    if fan.focus_metric and moment.type in MOVES_METRIC.get(fan.focus_metric, set()):
        score += 20
        reasons.append(f"+20 moves {fan.focus_metric}")
    if fan.mode == "analyst" and moment.type in ANALYST_FAVOURS:
        score += 10
        reasons.append("+10 analyst depth")
    elif fan.mode == "casual" and moment.type in ANALYST_FAVOURS:
        score -= 10
        reasons.append("-10 too technical for casual")
    involved = club or player or moment.type in ("half_time", "full_time")
    skip = False
    if fan.only_if_involved and not involved:
        score -= 40
        skip = True
        reasons.append("-40 not involved (only_if_involved)")
    return Ranking(score=max(0, min(score, 200)), involved=involved, skip=skip, reasons=reasons)
