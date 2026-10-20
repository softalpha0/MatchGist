"""Core data contracts shared by every stage of the pipeline.

Coordinates are metres on a 105 x 68 pitch, origin at the bottom-left corner
as seen on the broadcast feed. Match time is seconds since kick-off of the
first half (second half continues from 2700 s).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0


class Side(StrEnum):
    HOME = "home"
    AWAY = "away"

    @property
    def other(self) -> Side:
        return Side.AWAY if self is Side.HOME else Side.HOME


class Position(StrEnum):
    GK = "GK"
    DF = "DF"
    MF = "MF"
    FW = "FW"


class Player(BaseModel):
    id: str
    name: str
    short_name: str
    number: int
    position: Position
    side: Side
    # Ratings in [0, 1] that bias the simulator.
    passing: float = 0.6
    finishing: float = 0.5
    pace: float = 0.6
    tackling: float = 0.5


class Club(BaseModel):
    id: str
    name: str
    short: str
    colors: tuple[str, str]
    style: str = "balanced"  # possession | direct | pressing | balanced
    strength: float = 0.5


class MatchMeta(BaseModel):
    match_id: str
    seed: int
    home: Club
    away: Club
    venue: str
    competition: str = "Synthetic Premier Showcase"
    players: list[Player]


class EventType(StrEnum):
    KICK_OFF = "kick_off"
    PASS = "pass"
    CARRY = "carry"
    SHOT = "shot"
    GOAL = "goal"
    TACKLE = "tackle"
    INTERCEPTION = "interception"
    PRESSURE = "pressure"
    POSSESSION_CHANGE = "possession_change"
    FOUL = "foul"
    CARD = "card"
    SAVE = "save"
    CORNER = "corner"
    HALF_TIME = "half_time"
    FULL_TIME = "full_time"


class MatchEvent(BaseModel):
    """A single synthetic event as it would arrive from an event-data feed."""

    id: str
    seq: int
    t: float = Field(description="match clock, seconds")
    type: EventType
    side: Side | None = None
    player_id: str | None = None
    target_id: str | None = None
    x: float | None = None
    y: float | None = None
    end_x: float | None = None
    end_y: float | None = None
    outcome: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class Frame(BaseModel):
    """Tracking snapshot: every player's position plus the ball."""

    t: float
    period: int
    minute: float = Field(description="broadcast clock in minutes, e.g. 47.5 in the second half")
    ball: tuple[float, float]
    players: dict[str, tuple[float, float]]


Mode = Literal["analyst", "fan"]
Lang = Literal["en", "es", "fr", "pt"]


class Profile(BaseModel):
    """What a single viewer cares about. Same intelligence, different experience."""

    mode: Mode = "fan"
    language: Lang = "en"
    favourite_side: Side | None = None
    focus_player_id: str | None = None
    metric: str | None = Field(default=None, description="single metric pinned on screen, e.g. 'xg'")

    def cache_key(self) -> str:
        return f"{self.mode}|{self.language}|{self.favourite_side}|{self.focus_player_id}|{self.metric}"


InsightKind = Literal[
    "goal",
    "big_chance",
    "shot",
    "momentum_swing",
    "pressure_spike",
    "control_shift",
    "pass_of_note",
    "sprint",
    "milestone",
    "card",
    "half_time",
    "full_time",
]


class Insight(BaseModel):
    """A profile-agnostic piece of match intelligence produced by the interpret stage."""

    id: str
    t: float
    kind: InsightKind
    side: Side | None = None
    player_id: str | None = None
    importance: float = Field(ge=0, le=1)
    facts: dict[str, Any] = Field(default_factory=dict, description="every number a writer may cite")
    geo: dict[str, float] = Field(
        default_factory=dict, description="pitch coordinates for graphics, not for prose"
    )
    event_ids: list[str] = Field(default_factory=list)


CueSlot = Literal["lower_third", "player_tag", "ticker", "corner_bug", "full_panel", "pitch_arrow"]


class OverlayCue(BaseModel):
    """Timed, machine-readable instruction for a broadcast graphics engine.

    ``revision`` increases when an agent enriches a cue that is already on air
    (for example when the explanation arrives after the headline).
    """

    id: str
    insight_id: str
    kind: InsightKind
    revision: int = 0
    t_in: float
    t_out: float
    slot: CueSlot
    priority: int = Field(ge=0, le=100)
    anchor: dict[str, Any] = Field(default_factory=dict)
    headline: str
    body: str | None = None
    why: str | None = None
    chips: list[dict[str, Any]] = Field(default_factory=list)
    lang: str = "en"
    source: str = "director"
