"""Shared match state: the blackboard every agent reads from and the Interpret stage writes to.

All numbers that agents are allowed to cite come from here, which is what
lets the verifier reject invented statistics.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

from touchline.models import EventType, Frame, MatchEvent, MatchMeta, Side

SPRINT_SPEED = 7.0  # m/s, ~25 km/h
MAX_HUMAN_SPEED = 10.5  # m/s; anything faster in tracking is a repositioning artefact
WINDOW = 300.0  # seconds of match time used for rolling indices


@dataclass
class PlayerStats:
    distance: float = 0.0
    sprint_distance: float = 0.0
    sprints: int = 0
    top_speed: float = 0.0
    speed: float = 0.0
    passes: int = 0
    passes_completed: int = 0
    progressive_passes: int = 0
    difficult_completed: int = 0
    shots: int = 0
    goals: int = 0
    xg: float = 0.0
    tackles_won: int = 0
    interceptions: int = 0
    pressures: int = 0
    touches: int = 0
    in_sprint: bool = False

    def as_dict(self) -> dict:
        return {
            "distance_km": round(self.distance / 1000, 2),
            "sprints": self.sprints,
            "top_speed_kmh": round(self.top_speed * 3.6, 1),
            "passes": self.passes,
            "pass_accuracy": round(100 * self.passes_completed / self.passes) if self.passes else None,
            "progressive_passes": self.progressive_passes,
            "shots": self.shots,
            "goals": self.goals,
            "xg": round(self.xg, 2),
            "tackles_won": self.tackles_won,
            "interceptions": self.interceptions,
            "pressures": self.pressures,
        }


@dataclass
class TeamStats:
    passes: int = 0
    passes_completed: int = 0
    shots: int = 0
    shots_on_target: int = 0
    xg: float = 0.0
    goals: int = 0
    tackles_won: int = 0
    interceptions: int = 0
    pressures: int = 0
    fouls: int = 0
    corners: int = 0
    possession_time: float = 0.0
    final_third_entries: int = 0

    def as_dict(self, total_possession: float) -> dict:
        return {
            "goals": self.goals,
            "possession": round(100 * self.possession_time / total_possession) if total_possession else 50,
            "passes": self.passes,
            "pass_accuracy": round(100 * self.passes_completed / self.passes) if self.passes else None,
            "shots": self.shots,
            "shots_on_target": self.shots_on_target,
            "xg": round(self.xg, 2),
            "tackles_won": self.tackles_won,
            "interceptions": self.interceptions,
            "pressures": self.pressures,
            "fouls": self.fouls,
            "corners": self.corners,
            "final_third_entries": self.final_third_entries,
        }


@dataclass
class MatchState:
    meta: MatchMeta
    t: float = 0.0
    minute: float = 0.0
    period: int = 1
    score: list[int] = field(default_factory=lambda: [0, 0])
    possession: Side | None = None
    team: dict[Side, TeamStats] = field(
        default_factory=lambda: {Side.HOME: TeamStats(), Side.AWAY: TeamStats()}
    )
    players: dict[str, PlayerStats] = field(default_factory=dict)
    last_positions: dict[str, tuple[float, float]] = field(default_factory=dict)
    last_frame_t: float | None = None
    recent: deque[MatchEvent] = field(default_factory=lambda: deque(maxlen=4000))
    seen_ids: set[str] = field(default_factory=set)
    momentum_series: list[tuple[float, float]] = field(default_factory=list)
    control_series: list[tuple[float, float]] = field(default_factory=list)
    timeline: list[dict] = field(default_factory=list)
    ball: tuple[float, float] = (52.5, 34.0)

    def __post_init__(self) -> None:
        for p in self.meta.players:
            self.players.setdefault(p.id, PlayerStats())
        self.player_side = {p.id: p.side for p in self.meta.players}
        self.player_name = {p.id: p.name for p in self.meta.players}

    # ---------------------------------------------------------------- updates
    def apply_frame(self, frame: Frame) -> list[tuple[str, float]]:
        """Update physical metrics. Returns players who *started* a sprint this frame."""
        started: list[tuple[str, float]] = []
        if self.last_frame_t is not None:
            dt = frame.t - self.last_frame_t
            if dt > 0:
                for pid, pos in frame.players.items():
                    prev = self.last_positions.get(pid)
                    if prev is None:
                        continue
                    d = math.hypot(pos[0] - prev[0], pos[1] - prev[1])
                    speed = d / dt
                    if speed > MAX_HUMAN_SPEED:  # restart reposition, not running
                        continue
                    ps = self.players[pid]
                    ps.distance += d
                    ps.speed = speed
                    ps.top_speed = max(ps.top_speed, speed)
                    if speed >= SPRINT_SPEED:
                        ps.sprint_distance += d
                        if not ps.in_sprint:
                            ps.sprints += 1
                            ps.in_sprint = True
                            started.append((pid, speed))
                    elif speed < SPRINT_SPEED * 0.8:
                        ps.in_sprint = False
                if self.possession is not None:
                    self.team[self.possession].possession_time += dt
        self.last_frame_t = frame.t
        self.last_positions = dict(frame.players)
        self.t = frame.t
        self.minute = frame.minute
        self.period = frame.period
        self.ball = frame.ball
        return started

    def apply_event(self, ev: MatchEvent) -> None:
        self.recent.append(ev)
        self.seen_ids.add(ev.id)
        side = ev.side
        ts = self.team[side] if side is not None else None
        ps = self.players.get(ev.player_id) if ev.player_id else None
        if ps:
            ps.touches += 1
        match ev.type:
            case EventType.PASS:
                assert ts and ps
                ts.passes += 1
                ps.passes += 1
                self.possession = side
                if ev.outcome == "complete":
                    ts.passes_completed += 1
                    ps.passes_completed += 1
                    if ev.data.get("difficulty", 0) >= 0.45:
                        ps.difficult_completed += 1
                    if ev.data.get("progressive"):
                        ps.progressive_passes += 1
                    if (
                        ev.end_x is not None
                        and ev.x is not None
                        and self._in_final_third(side, ev.end_x)
                        and not self._in_final_third(side, ev.x)
                    ):
                        ts.final_third_entries += 1
            case EventType.SHOT:
                assert ts and ps
                ts.shots += 1
                ps.shots += 1
                xg = float(ev.data.get("xg", 0))
                ts.xg += xg
                ps.xg += xg
                if ev.outcome in ("goal", "saved"):
                    ts.shots_on_target += 1
            case EventType.GOAL:
                assert ts and ps
                ts.goals += 1
                ps.goals += 1
                self.score = list(ev.data.get("score", self.score))
            case EventType.TACKLE:
                if ev.outcome == "won" and ts and ps:
                    ts.tackles_won += 1
                    ps.tackles_won += 1
            case EventType.INTERCEPTION:
                if ts and ps:
                    ts.interceptions += 1
                    ps.interceptions += 1
            case EventType.PRESSURE:
                if ts and ps:
                    ts.pressures += 1
                    ps.pressures += 1
            case EventType.FOUL:
                if ts:
                    ts.fouls += 1
            case EventType.CORNER:
                if ts:
                    ts.corners += 1
            case EventType.POSSESSION_CHANGE:
                self.possession = side
            case _:
                pass

    def _in_final_third(self, side: Side | None, x: float) -> bool:
        if side is None:
            return False
        attacking_right = (side is Side.HOME) == (self.period == 1)
        return x > 70 if attacking_right else x < 35

    # ---------------------------------------------------------------- indices
    def window_events(self, seconds: float = WINDOW) -> list[MatchEvent]:
        lo = self.t - seconds
        return [e for e in self.recent if e.t >= lo]

    def momentum(self, seconds: float = WINDOW) -> float:
        """Signed momentum in [-1, 1]; positive favours home.

        Threat-weighted: xG counts most, then final-third passes, pressures
        won high up and tackles. Older events decay exponentially.
        """
        score = {Side.HOME: 0.0, Side.AWAY: 0.0}
        for e in self.window_events(seconds):
            if e.side is None:
                continue
            w = math.exp(-(self.t - e.t) / (seconds / 2))
            if e.type is EventType.SHOT:
                score[e.side] += w * (1.0 + 6 * float(e.data.get("xg", 0)))
            elif e.type is EventType.PASS and e.outcome == "complete" and e.end_x is not None:
                if self._in_final_third(e.side, e.end_x):
                    score[e.side] += 0.25 * w
                else:
                    score[e.side] += 0.03 * w
            elif e.type in (EventType.TACKLE, EventType.INTERCEPTION) and e.outcome != "lost":
                score[e.side] += 0.15 * w
            elif e.type is EventType.CORNER:
                score[e.side] += 0.4 * w
        total = score[Side.HOME] + score[Side.AWAY]
        if total < 0.5:
            return 0.0
        return round((score[Side.HOME] - score[Side.AWAY]) / total, 3)

    def control(self, seconds: float = 180.0) -> dict:
        """Control vs chaos over the window.

        Control rises with long, completed possession chains; chaos rises with
        turnovers per minute and the share of possessions lasting < 3 passes.
        Returns a 0..100 chaos index plus the inputs that explain it.
        """
        evs = self.window_events(seconds)
        if not evs:
            return {"chaos": 50, "turnovers_per_min": 0, "avg_chain": 0, "pass_accuracy": None}
        span = max(min(seconds, self.t) / 60, 0.5)
        turnovers = sum(1 for e in evs if e.type is EventType.POSSESSION_CHANGE)
        passes = [e for e in evs if e.type is EventType.PASS]
        completed = sum(1 for e in passes if e.outcome == "complete")
        chains: list[int] = []
        cur = 0
        for e in evs:
            if e.type is EventType.PASS and e.outcome == "complete":
                cur += 1
            elif e.type is EventType.POSSESSION_CHANGE:
                chains.append(cur)
                cur = 0
        chains.append(cur)
        avg_chain = sum(chains) / len(chains)
        tpm = turnovers / span
        acc = completed / len(passes) if passes else 0.0
        fouls = sum(1 for e in evs if e.type is EventType.FOUL) / span
        chaos = 100 / (1 + math.exp(-(1.1 * tpm - 0.45 * avg_chain - 4.0 * (acc - 0.78) + 2.0 * fouls - 2.2)))
        return {
            "chaos": round(chaos),
            "turnovers_per_min": round(tpm, 2),
            "avg_chain": round(avg_chain, 1),
            "pass_accuracy": round(100 * acc) if passes else None,
        }

    def rhythm(self, seconds: float = 120.0) -> dict:
        """Tempo: on-ball actions per minute and average pass speed."""
        evs = [
            e
            for e in self.window_events(seconds)
            if e.type in (EventType.PASS, EventType.CARRY, EventType.SHOT)
        ]
        span = max(min(seconds, self.t) / 60, 0.5)
        speeds = [float(e.data.get("speed", 0)) for e in evs if e.type is EventType.PASS]
        return {
            "actions_per_min": round(len(evs) / span, 1),
            "avg_pass_speed_kmh": round(3.6 * sum(speeds) / len(speeds), 1) if speeds else None,
        }

    def pressure_index(self, side: Side, seconds: float = 120.0) -> float:
        """Pressures applied by ``side`` per minute in the window."""
        span = max(min(seconds, self.t) / 60, 0.5)
        return round(
            sum(1 for e in self.window_events(seconds) if e.type is EventType.PRESSURE and e.side is side)
            / span,
            2,
        )

    def snapshot(self) -> dict:
        """Compact JSON-safe view used by the UI, tools and agents."""
        total = self.team[Side.HOME].possession_time + self.team[Side.AWAY].possession_time
        return {
            "t": self.t,
            "minute": self.minute,
            "period": self.period,
            "score": self.score,
            "possession": self.possession,
            "home": self.team[Side.HOME].as_dict(total),
            "away": self.team[Side.AWAY].as_dict(total),
            "momentum": self.momentum(),
            "control": self.control(),
            "rhythm": self.rhythm(),
            "pressure": {"home": self.pressure_index(Side.HOME), "away": self.pressure_index(Side.AWAY)},
        }

    def player_snapshot(self, pid: str) -> dict:
        return {
            "id": pid,
            "name": self.player_name.get(pid),
            "side": self.player_side.get(pid),
            **self.players[pid].as_dict(),
        }
