"""Match State: the shared blackboard every stage reads from. The Stats Engine is its only writer.

``snapshot()`` is the contract with the agents: every number an agent may cite must appear in it, which
is what the Verifier checks in M3.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from app.moments.models import Moment
from app.simulator.schema import Match
from app.stats.metrics import normalise_momentum, pct

WINDOW_S = 300.0  # five minutes of match time for rolling metrics


@dataclass
class TeamStats:
    passes: int = 0
    passes_completed: int = 0
    progressive_passes: int = 0
    final_third_entries: int = 0
    shots: int = 0
    shots_on_target: int = 0
    goals: int = 0
    xg: float = 0.0
    top_shot_speed_kmh: float = 0.0
    tackles_won: int = 0
    interceptions: int = 0
    pressures: int = 0
    fouls: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    possession_s: float = 0.0
    players_on_pitch: int = 11


@dataclass
class PlayerStats:
    passes: int = 0
    passes_completed: int = 0
    elite_passes: int = 0
    shots: int = 0
    goals: int = 0
    xg: float = 0.0
    top_shot_speed_kmh: float = 0.0
    tackles_won: int = 0
    interceptions: int = 0
    carries: int = 0
    carry_m: float = 0.0
    yellow_cards: int = 0
    sent_off: bool = False
    sprints: int = 0
    top_speed_kmh: float = 0.0
    distance_km: int = 0  # last whole-kilometre milestone from the tracking data

    def as_dict(self) -> dict[str, Any]:
        return {
            "passes": self.passes,
            "pass_accuracy": pct(self.passes_completed, self.passes),
            "elite_passes": self.elite_passes,
            "shots": self.shots,
            "goals": self.goals,
            "xg": round(self.xg, 2),
            "top_shot_speed_kmh": round(self.top_shot_speed_kmh, 1),
            "tackles_won": self.tackles_won,
            "interceptions": self.interceptions,
            "carry_m": round(self.carry_m),
            "sprints": self.sprints,
            "top_speed_kmh": round(self.top_speed_kmh, 1),
            "distance_km": self.distance_km,
        }


@dataclass
class MatchState:
    match: Match
    t: float = 0.0  # continuous match seconds (half-time break excluded)
    match_clock: str = "00:00"
    period: int = 1
    status: str = "pre_match"  # pre_match | first_half | half_time | second_half | full_time
    possession: str | None = None
    teams: dict[str, TeamStats] = field(default_factory=dict)
    players: dict[str, PlayerStats] = field(default_factory=dict)
    window: deque[tuple[float, str, int]] = field(default_factory=deque)  # (t, team, momentum points)
    pass_window: deque[tuple[float, str, float]] = field(default_factory=deque)  # (t, team, pressure)
    possession_window: deque[tuple[float, float, str]] = field(default_factory=deque)  # (start, end, team)
    momentum_series: list[tuple[float, int]] = field(default_factory=list)  # (minute, momentum)
    pressure_series: dict[str, list[tuple[float, float | None]]] = field(default_factory=dict)
    moments: list[Moment] = field(default_factory=list)
    events_seen: int = 0

    def __post_init__(self) -> None:
        self.home_id = self.match.home.club_id
        self.away_id = self.match.away.club_id
        self.teams = {self.home_id: TeamStats(), self.away_id: TeamStats()}
        self.pressure_series = {self.home_id: [], self.away_id: []}
        self.names = {p.player_id: p.name for c in (self.match.home, self.match.away) for p in c.players}
        self.club_names = {self.home_id: self.match.home.name, self.away_id: self.match.away.name}
        for pid in self.names:
            self.players.setdefault(pid, PlayerStats())

    # ------------------------------------------------------------------ derived values
    @property
    def minute(self) -> int:
        """Broadcast minute: 1-based, so 00:30 is the 1st minute."""
        secs = int(self.match_clock.split(":")[0]) * 60 + int(self.match_clock.split(":")[1])
        return secs // 60 + 1

    @property
    def score(self) -> tuple[int, int]:
        return self.teams[self.home_id].goals, self.teams[self.away_id].goals

    def other(self, team_id: str) -> str:
        return self.away_id if team_id == self.home_id else self.home_id

    def momentum(self) -> int:
        pts = {self.home_id: 0, self.away_id: 0}
        for _, team, p in self.window:
            pts[team] += p
        return normalise_momentum(pts[self.home_id], pts[self.away_id])

    def pressure_index(self, team_id: str) -> float | None:
        """Mean pressure faced by ``team_id``'s passes in the last five minutes (0-1)."""
        vals = [p for _, team, p in self.pass_window if team == team_id]
        return round(sum(vals) / len(vals), 2) if vals else None

    def possession_pct(self, team_id: str, rolling: bool = False) -> int | None:
        if not rolling:
            total = sum(ts.possession_s for ts in self.teams.values())
            return pct(self.teams[team_id].possession_s, total)
        lo = self.t - WINDOW_S
        mine = total = 0.0
        for start, end, team in self.possession_window:
            span = max(0.0, end - max(start, lo))
            total += span
            if team == team_id:
                mine += span
        return pct(mine, total)

    # ------------------------------------------------------------------ snapshot
    def team_snapshot(self, team_id: str) -> dict[str, Any]:
        ts = self.teams[team_id]
        return {
            "club_id": team_id,
            "name": self.club_names[team_id],
            "goals": ts.goals,
            "possession": self.possession_pct(team_id),
            "possession_5min": self.possession_pct(team_id, rolling=True),
            "passes": ts.passes,
            "pass_accuracy": pct(ts.passes_completed, ts.passes),
            "progressive_passes": ts.progressive_passes,
            "final_third_entries": ts.final_third_entries,
            "shots": ts.shots,
            "shots_on_target": ts.shots_on_target,
            "xg": round(ts.xg, 2),
            "top_shot_speed_kmh": round(ts.top_shot_speed_kmh, 1),
            "tackles_won": ts.tackles_won,
            "interceptions": ts.interceptions,
            "pressures": ts.pressures,
            "fouls": ts.fouls,
            "yellow_cards": ts.yellow_cards,
            "red_cards": ts.red_cards,
            "players_on_pitch": ts.players_on_pitch,
            "pressure_index": self.pressure_index(team_id),
        }

    def snapshot(self, players: bool = False) -> dict[str, Any]:
        """JSON-safe view of the whole state. Every agent-citable number lives here."""
        snap: dict[str, Any] = {
            "match_id": self.match.match_id,
            "match_clock": self.match_clock,
            "minute": self.minute,
            "period": self.period,
            "status": self.status,
            "score": list(self.score),
            "possession": self.possession,
            "momentum": self.momentum(),
            "home": self.team_snapshot(self.home_id),
            "away": self.team_snapshot(self.away_id),
            "events_seen": self.events_seen,
        }
        if players:
            snap["players"] = {
                pid: {"name": self.names[pid], **ps.as_dict()}
                for pid, ps in self.players.items()
                if ps.passes or ps.shots or ps.tackles_won or ps.interceptions
            }
        return snap
