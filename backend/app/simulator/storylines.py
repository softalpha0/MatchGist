"""Storylines: steer a seeded match toward a narrative without breaking determinism.

A storyline does two things:

1. ``StoryPlan`` biases the simulator (finishing and shooting multipliers by minute, a forced
   red card), which makes the storyline likely.
2. ``satisfied`` checks the finished match. The generator tries derived sub-seeds in a fixed
   order until one satisfies the storyline, so the same ``(seed, storyline)`` always gives the
   same match.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.simulator.schema import Storyline

HOME, AWAY = "home", "away"


@dataclass
class StoryPlan:
    storyline: Storyline
    leader: str | None = None  # comeback: the side that leads early and is then caught
    red_side: str | None = None
    red_minute: float = 999.0

    def finishing(self, side: str, minute: float) -> float:
        """Multiplier on goal probability for ``side`` at ``minute``."""
        if self.storyline == "comeback":
            if minute < 60:
                return 2.0 if side == self.leader else 0.4
            if minute >= 68:
                return 0.3 if side == self.leader else 2.8
        if self.storyline == "late_drama":
            return 3.2 if minute >= 85 else 0.6
        return 1.0

    def shooting(self, side: str, minute: float) -> float:
        """Multiplier on the chance that a player in range shoots."""
        if self.storyline == "comeback" and minute >= 68 and side != self.leader:
            return 2.2
        if self.storyline == "late_drama" and minute >= 85:
            return 2.8
        return 1.0

    def force_red(self, side: str, minute: float) -> bool:
        """True when ``side`` is due its scripted red card."""
        return self.storyline == "red_card" and side == self.red_side and minute >= self.red_minute


def plan_for(storyline: Storyline, rng: random.Random) -> StoryPlan:
    if storyline == "comeback":
        return StoryPlan(storyline, leader=rng.choice([HOME, AWAY]))
    if storyline == "red_card":
        return StoryPlan(storyline, red_side=rng.choice([HOME, AWAY]), red_minute=rng.uniform(25, 70))
    return StoryPlan(storyline)


def _minute(ev: dict[str, Any]) -> float:
    m, s = ev["match_clock"].split(":")
    return int(m) + int(s) / 60


def goals(events: Sequence[dict[str, Any]], home_id: str) -> list[tuple[int, float, str]]:
    """(period, minute, side) for every goal, in order."""
    return [
        (ev["period"], _minute(ev), HOME if ev["team_id"] == home_id else AWAY)
        for ev in events
        if ev["type"] == "shot" and ev["outcome"] == "goal"
    ]


def score_at(events: Sequence[dict[str, Any]], home_id: str, period: int, minute: float) -> tuple[int, int]:
    h = a = 0
    for p, m, side in goals(events, home_id):
        if (p, m) < (period, minute):
            h, a = (h + 1, a) if side == HOME else (h, a + 1)
    return h, a


def satisfied(storyline: Storyline, events: Sequence[dict[str, Any]], home_id: str) -> bool:
    """Does a finished match deliver the storyline?"""
    if storyline == "none":
        return True
    if storyline == "red_card":
        return any(ev["type"] == "foul" and ev["card"] == "red" for ev in events)
    final = score_at(events, home_id, 9, 0)
    if storyline == "comeback":
        h70, a70 = score_at(events, home_id, 2, 70)
        if h70 == a70:
            return False
        trailing_final_diff = (final[0] - final[1]) if h70 < a70 else (final[1] - final[0])
        return trailing_final_diff >= 0
    if storyline == "late_drama":
        late = [g for g in goals(events, home_id) if g[0] == 2 and g[1] >= 85]
        if not late:
            return False
        period, minute, side = late[-1]
        h, a = score_at(events, home_id, period, minute)
        before = h - a if side == HOME else a - h
        after = final[0] - final[1] if side == HOME else final[1] - final[0]
        # decisive: it turned a draw into a win, or a defeat into a draw, and it stood
        return before in (-1, 0) and after == before + 1
    return False
