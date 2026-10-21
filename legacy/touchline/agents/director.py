"""Director: decides what goes on screen, where, for how long, for whom.

Deterministic by design. A broadcast graphics engine needs a cue the instant a
moment happens, so headlines and stat chips are rendered here without a model
call; the language agents enrich the cue a moment later (``revision`` + 1).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from touchline.agents import templates
from touchline.models import CueSlot, Insight, OverlayCue, Profile

# kind -> (slot, on-screen seconds of match time, anchor to player?)
LAYOUT: dict[str, tuple[CueSlot, float, bool]] = {
    "goal": ("full_panel", 25, False),
    "big_chance": ("lower_third", 12, True),
    "shot": ("player_tag", 6, True),
    "momentum_swing": ("corner_bug", 30, False),
    "pressure_spike": ("lower_third", 14, False),
    "control_shift": ("corner_bug", 30, False),
    "pass_of_note": ("pitch_arrow", 8, True),
    "sprint": ("player_tag", 5, True),
    "milestone": ("ticker", 15, True),
    "card": ("lower_third", 12, True),
    "half_time": ("full_panel", 60, False),
    "full_time": ("full_panel", 600, False),
}

# Chips are the numbers a graphics template shows next to the headline.
CHIPS: dict[str, list[tuple[str, str, str]]] = {
    # kind -> [(fact key, label, unit)]
    "goal": [("xg", "xG", ""), ("shot_speed_kmh", "Shot", "km/h"), ("distance_m", "Distance", "m")],
    "big_chance": [("xg", "xG", ""), ("distance_m", "Distance", "m")],
    "shot": [("shot_speed_kmh", "Shot", "km/h"), ("xg", "xG", "")],
    "momentum_swing": [("momentum_pct", "Threat share", "%"), ("shots_in_window", "Shots (5')", "")],
    "pressure_spike": [("pressures_per_min", "Pressures/min", ""), ("turnovers_forced", "Turnovers", "")],
    "control_shift": [("chaos", "Chaos", "/100"), ("avg_chain", "Passes/move", "")],
    "pass_of_note": [
        ("difficulty", "Difficulty", "/10"),
        ("length_m", "Length", "m"),
        ("ball_speed_kmh", "Ball", "km/h"),
        ("accuracy", "Accuracy", "%"),
    ],
    "sprint": [("speed_kmh", "Speed", "km/h"), ("distance_km", "Distance", "km")],
    "milestone": [("value", "Total", "")],
    "card": [("team_fouls", "Team fouls", "")],
    "half_time": [("home_xg", "xG home", ""), ("away_xg", "xG away", "")],
    "full_time": [("home_xg", "xG home", ""), ("away_xg", "xG away", "")],
}

FAN_KINDS = {
    "goal",
    "big_chance",
    "shot",
    "momentum_swing",
    "control_shift",
    "card",
    "half_time",
    "full_time",
    "sprint",
    "milestone",
    "pressure_spike",
}


@dataclass
class Director:
    profile: Profile
    on_air: dict[CueSlot, OverlayCue] = field(default_factory=dict)
    dropped: int = 0

    def wants(self, ins: Insight) -> bool:
        """Editorial filter per profile: analysts get everything, fans get the story."""
        p = self.profile
        if p.focus_player_id and ins.player_id == p.focus_player_id:
            return True
        if p.mode == "analyst":
            return True
        if ins.kind not in FAN_KINDS:
            return False
        if ins.kind == "sprint":
            return bool(ins.facts.get("fastest_in_match"))
        if ins.kind == "milestone":
            return ins.facts.get("milestone") == "distance_km"
        return True

    def priority(self, ins: Insight) -> int:
        p = self.profile
        score = ins.importance * 80
        if p.focus_player_id and ins.player_id == p.focus_player_id:
            score += 20
        if p.favourite_side and ins.side == p.favourite_side:
            score += 10
        return int(min(100, score))

    def chips(self, ins: Insight) -> list[dict]:
        derived = templates.derive(ins.facts, self.profile.language)
        spec = CHIPS.get(ins.kind, [])
        if self.profile.mode == "fan":
            spec = spec[:1]
        out = [
            {"label": label, "value": derived[key], "unit": unit}
            for key, label, unit in spec
            if derived.get(key) not in (None, "")
        ]
        metric = self.profile.metric
        if metric and metric in derived and all(c["label"] != metric for c in out):
            out.append({"label": metric, "value": derived[metric], "unit": "", "pinned": True})
        return out

    def headline(self, ins: Insight) -> str:
        p = self.profile
        text = templates.render(ins.kind, ins.facts, p.language, "headline")
        if p.focus_player_id and ins.player_id == p.focus_player_id:
            return templates.prefix(p.language, "focus") + text
        if (
            p.favourite_side
            and ins.side is not None
            and ins.kind in ("goal", "big_chance", "momentum_swing", "card")
        ):
            key = "fav_for" if ins.side == p.favourite_side else "fav_against"
            return templates.prefix(p.language, key) + text
        return text

    def cue_for(self, ins: Insight) -> OverlayCue | None:
        """Build the instant cue, or ``None`` if this viewer should not see it."""
        if not self.wants(ins):
            return None
        slot, seconds, anchored = LAYOUT[ins.kind]
        prio = self.priority(ins)
        current = self.on_air.get(slot)
        exclusive = slot in ("lower_third", "full_panel", "corner_bug")
        must_air = ins.importance >= 1.0  # goals and period ends always make air
        if exclusive and not must_air and current and current.t_out > ins.t and current.priority > prio:
            self.dropped += 1
            return None
        anchor: dict = {}
        if anchored and ins.player_id:
            anchor["player_id"] = ins.player_id
        if ins.side is not None:
            anchor["side"] = ins.side.value
        anchor.update(ins.geo)
        cue = OverlayCue(
            id=f"c-{ins.id}",
            insight_id=ins.id,
            kind=ins.kind,
            t_in=ins.t,
            t_out=ins.t + seconds,
            slot=slot,
            priority=prio,
            anchor=anchor,
            headline=self.headline(ins),
            chips=self.chips(ins),
            lang=self.profile.language,
            source="director",
        )
        if exclusive:
            self.on_air[slot] = cue
        return cue
