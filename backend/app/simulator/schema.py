"""Event schema v1 (SPEC section 8.2): one Pydantic model per event type, plus clubs and matches.

Coordinates are **team-relative**: ``x`` runs 0-105 from the acting team's own goal to the goal it
attacks, ``y`` runs 0-68. The acting team is ``team_id``. Renderers mirror the away side and the
second half. ``match_clock`` restarts at 45:00 in the second half, so ordering is by
``(period, match_clock)``; ``seq`` is strictly increasing across the whole match.
"""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator

PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0
CLOCK_RE = re.compile(r"^\d{2,3}:[0-5]\d$")

Position = Literal["GK", "DF", "MF", "FW"]
Storyline = Literal["none", "comeback", "red_card", "late_drama"]
X = Annotated[float, Field(ge=0, le=PITCH_LENGTH)]
Y = Annotated[float, Field(ge=0, le=PITCH_WIDTH)]
Unit = Annotated[float, Field(ge=0, le=1)]


# --------------------------------------------------------------------------- clubs
class PlayerRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_id: str = Field(pattern=r"^[A-Z]{3}-\d{2}$")
    name: str
    shirt_number: int = Field(ge=1, le=99)
    position: Position
    starter: bool
    pace: int = Field(ge=1, le=100)
    passing: int = Field(ge=1, le=100)
    shooting: int = Field(ge=1, le=100)
    defending: int = Field(ge=1, le=100)


class Club(BaseModel):
    model_config = ConfigDict(extra="forbid")

    club_id: str = Field(pattern=r"^[A-Z]{3}$")
    name: str
    short_name: str
    colors: tuple[str, str]
    style: Literal["possession", "direct", "pressing", "balanced"] = "balanced"
    players: list[PlayerRecord]

    def starters(self) -> list[PlayerRecord]:
        return [p for p in self.players if p.starter]

    def bench(self) -> list[PlayerRecord]:
        return [p for p in self.players if not p.starter]


# --------------------------------------------------------------------------- events
class EventBase(BaseModel):
    """Fields shared by every event."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    match_id: str
    seq: int = Field(ge=1)
    match_clock: str = Field(description="MM:SS; second half starts at 45:00")
    period: Literal[1, 2]
    team_id: str | None = None
    player_id: str | None = None
    x: X | None = None
    y: Y | None = None
    meta: dict[str, Any] = Field(default_factory=dict)

    @field_validator("match_clock")
    @classmethod
    def _clock(cls, v: str) -> str:
        if not CLOCK_RE.match(v):
            raise ValueError(f"bad match_clock {v!r}")
        return v

    @property
    def clock_seconds(self) -> int:
        m, s = self.match_clock.split(":")
        return int(m) * 60 + int(s)


class KickoffEvent(EventBase):
    type: Literal["kickoff"] = "kickoff"


class HalfTimeEvent(EventBase):
    type: Literal["half_time"] = "half_time"


class FullTimeEvent(EventBase):
    type: Literal["full_time"] = "full_time"


class PassEvent(EventBase):
    type: Literal["pass"] = "pass"
    end_x: X
    end_y: Y
    outcome: Literal["complete", "incomplete"]
    receiver_id: str | None
    pressure: Unit = Field(description="0 = unchallenged, 1 = opponent on top of the passer")
    speed_kmh: float | None = Field(default=None, ge=0, description="ball speed")


class CarryEvent(EventBase):
    type: Literal["carry"] = "carry"
    end_x: X
    end_y: Y
    distance_m: float = Field(ge=0)
    speed_kmh: float = Field(ge=0)


class ShotEvent(EventBase):
    type: Literal["shot"] = "shot"
    outcome: Literal["goal", "saved", "off_target", "blocked"]
    speed_kmh: float = Field(ge=0)
    xg: Unit
    pressure: Unit = 0.0


class TackleEvent(EventBase):
    type: Literal["tackle"] = "tackle"
    outcome: Literal["won", "lost"]
    opponent_id: str


class InterceptionEvent(EventBase):
    type: Literal["interception"] = "interception"


class FoulEvent(EventBase):
    type: Literal["foul"] = "foul"
    card: Literal["none", "yellow", "red"]


class PossessionChangeEvent(EventBase):
    type: Literal["possession_change"] = "possession_change"
    from_team: str
    to_team: str
    cause: Literal[
        "interception", "tackle", "save", "block", "goal_kick", "kick_off", "foul", "throw_in", "half_time"
    ]


class PressureEvent(EventBase):
    type: Literal["pressure"] = "pressure"
    target_player_id: str
    intensity: Unit


class SubstitutionEvent(EventBase):
    type: Literal["substitution"] = "substitution"
    player_off: str
    player_on: str


MatchEvent = Annotated[
    KickoffEvent
    | HalfTimeEvent
    | FullTimeEvent
    | PassEvent
    | CarryEvent
    | ShotEvent
    | TackleEvent
    | InterceptionEvent
    | FoulEvent
    | PossessionChangeEvent
    | PressureEvent
    | SubstitutionEvent,
    Field(discriminator="type"),
]
EVENT_ADAPTER: TypeAdapter[MatchEvent] = TypeAdapter(MatchEvent)
EVENT_TYPES = (
    "kickoff",
    "half_time",
    "full_time",
    "pass",
    "carry",
    "shot",
    "tackle",
    "interception",
    "foul",
    "possession_change",
    "pressure",
    "substitution",
)


def parse_event(data: dict[str, Any]) -> MatchEvent:
    """Validate one raw event dict into its typed model."""
    return EVENT_ADAPTER.validate_python(data)


# --------------------------------------------------------------------------- match
class Match(BaseModel):
    """A fully simulated match: metadata plus the ordered event list."""

    match_id: str
    seed: int
    sim_seed: int = Field(description="sub-seed actually simulated (differs from seed for storylines)")
    storyline: Storyline
    home: Club
    away: Club
    venue: str
    final_score: tuple[int, int]
    events: list[MatchEvent]
