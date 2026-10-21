"""Delivery adapters: turn a verified message into what a channel actually carries.

``broadcast`` becomes a timed overlay cue a graphics engine can render (SPEC section 10.2). The other
channels are message objects shown on the device simulators in the UI (and, as a stretch, real SMS).
"""

from __future__ import annotations

from typing import Any

from app.moments.models import Moment

# moment type -> (slot, on-screen milliseconds)
OVERLAY_LAYOUT: dict[str, tuple[str, int]] = {
    "goal": ("top_bar", 10_000),
    "red_card": ("lower_third", 8_000),
    "big_chance": ("lower_third", 7_000),
    "momentum_swing": ("side_panel", 12_000),
    "pressure_spike": ("side_panel", 10_000),
    "elite_pass": ("player_tag", 6_000),
    "yellow_card": ("player_tag", 5_000),
    "half_time": ("lower_third", 15_000),
    "full_time": ("lower_third", 20_000),
}
OVERLAY_DATA_KEYS = (
    "player",
    "receiver",
    "team",
    "score",
    "xg",
    "shot_speed_kmh",
    "distance_m",
    "difficulty",
    "pressure",
    "momentum_now",
    "pressure_index",
    "home_xg",
    "away_xg",
    "home_possession",
    "away_possession",
)


def match_ms(moment: Moment) -> int:
    """Broadcast clock in milliseconds (second half continues from 45:00)."""
    m, s = moment.match_clock.split(":")
    return (int(m) * 60 + int(s)) * 1000


def overlay_cue(moment: Moment, text: str, cue_no: int) -> dict[str, Any]:
    slot, duration = OVERLAY_LAYOUT.get(moment.type, ("lower_third", 6_000))
    return {
        "cue_id": f"cue-{cue_no:04d}",
        "match_clock": moment.match_clock,
        "period": moment.period,
        "show_at_ms": match_ms(moment),
        "duration_ms": duration,
        "slot": slot,
        "template": moment.type,
        "anchor_player_id": moment.player_id,
        "data": {k: moment.facts[k] for k in OVERLAY_DATA_KEYS if k in moment.facts},
        "text": text,
    }
