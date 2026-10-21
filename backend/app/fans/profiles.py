"""Fan profile (SPEC section 5) and loading of the demo personas in ``data/fans.json``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.config import DATA_DIR

Mode = Literal["analyst", "casual", "club_focus", "player_focus", "single_metric"]
Channel = Literal["broadcast", "sms", "chat", "voice", "watch", "push"]
Language = Literal["en", "hi", "id", "pt-BR", "ar", "pcm"]
FocusMetric = Literal["xg", "possession", "momentum", "pressure", "pass_accuracy", "shot_speed"]


class FanProfile(BaseModel):
    """What one fan has and wants. ``None`` budgets mean unlimited."""

    model_config = ConfigDict(extra="forbid")

    fan_id: str = Field(pattern=r"^[a-z0-9_]+$")
    display_name: str
    language: Language
    mode: Mode
    favorite_club: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    favorite_player: str | None = Field(default=None, pattern=r"^[A-Z]{3}-\d{2}$")
    focus_metric: FocusMetric | None = None
    channel: Channel
    data_budget_kb: float | None = Field(default=None, gt=0)
    max_pings: int | None = Field(default=None, ge=1)
    only_if_involved: bool = False
    quiet_after_minute: int | None = Field(default=None, ge=0, le=120)

    @model_validator(mode="after")
    def _consistent(self) -> FanProfile:
        if self.mode == "player_focus" and not self.favorite_player:
            raise ValueError("player_focus mode needs favorite_player")
        if self.mode == "club_focus" and not self.favorite_club:
            raise ValueError("club_focus mode needs favorite_club")
        if self.mode == "single_metric" and not self.focus_metric:
            raise ValueError("single_metric mode needs focus_metric")
        if self.only_if_involved and not (self.favorite_club or self.favorite_player):
            raise ValueError("only_if_involved needs a favorite club or player")
        return self


def load_fans(path: Path | None = None) -> list[FanProfile]:
    """Load and validate the demo personas."""
    raw = json.loads((path or DATA_DIR / "fans.json").read_text(encoding="utf-8"))
    return [FanProfile.model_validate(f) for f in raw["fans"]]
