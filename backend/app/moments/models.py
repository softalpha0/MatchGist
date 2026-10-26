"""Moment: a candidate key moment with its base importance and the facts behind it."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

MomentType = Literal[
    "goal",
    "red_card",
    "big_chance",
    "momentum_swing",
    "half_time",
    "full_time",
    "pressure_spike",
    "elite_pass",
    "yellow_card",
]

# SPEC 9.1 base importance
BASE_SCORE: dict[str, int] = {
    "goal": 100,
    "red_card": 85,
    "big_chance": 60,
    "momentum_swing": 55,
    "half_time": 50,
    "full_time": 90,
    "pressure_spike": 40,
    "elite_pass": 30,
    "yellow_card": 25,
}


class Moment(BaseModel):
    moment_id: str
    type: MomentType
    match_clock: str
    period: int
    minute: int
    team_id: str | None = None
    player_id: str | None = None
    involved_player_ids: list[str] = Field(default_factory=list, description="scorer, assister, receiver")
    base_score: int = Field(ge=0, le=100)
    facts: dict[str, Any] = Field(default_factory=dict, description="the only numbers agents may cite")
    event_id: str | None = None
    source_event_ids: list[str] = Field(
        default_factory=list, description="the events leading up to and including the trigger, oldest first"
    )
