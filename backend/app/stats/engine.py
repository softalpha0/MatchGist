"""Stats Engine: folds each event into the Match State. Pure code: the only source of numbers."""

from __future__ import annotations

from app.simulator.schema import MatchEvent
from app.state.match_state import WINDOW_S, MatchState
from app.stats.metrics import (
    into_final_third,
    is_progressive,
    momentum_points,
    pass_difficulty,
)

HALF_S = 45 * 60
SAMPLE_EVERY_S = 60.0


class StatsEngine:
    def __init__(self, state: MatchState):
        self.state = state
        self.half1_end = 0.0
        self.last_t = 0.0
        self.next_sample = SAMPLE_EVERY_S
        self.last_pass_difficulty: dict[str, float] = {}  # event_id -> difficulty, for the detector

    def to_seconds(self, ev: MatchEvent) -> float:
        """Continuous match seconds: the second half continues from where the first ended."""
        return float(ev.clock_seconds) if ev.period == 1 else self.half1_end + ev.clock_seconds - HALF_S

    def apply(self, ev: MatchEvent) -> list[float]:
        """Fold one event into the state. Returns the sample times (minutes) crossed, for periodic checks."""
        s = self.state
        t = self.to_seconds(ev)
        self._advance_clock(t)
        s.match_clock, s.period = ev.match_clock, ev.period
        s.events_seen += 1
        team = ev.team_id
        ts = s.teams[team] if team else None
        ps = s.players.get(ev.player_id) if ev.player_id else None

        match ev.type:
            case "kickoff":
                s.status = "first_half" if ev.period == 1 else "second_half"
                s.possession = team
            case "half_time":
                s.status = "half_time"
                self.half1_end = t
            case "full_time":
                s.status = "full_time"
            case "pass":
                assert ts and ps
                s.possession = team
                ts.passes += 1
                ps.passes += 1
                s.pass_window.append((t, team, ev.pressure))
                prog = is_progressive(ev.x or 0, ev.end_x)
                if ev.outcome == "complete":
                    ts.passes_completed += 1
                    ps.passes_completed += 1
                    if prog:
                        ts.progressive_passes += 1
                    if into_final_third(ev.x or 0, ev.end_x):
                        ts.final_third_entries += 1
                diff = pass_difficulty(ev.x or 0, ev.y or 0, ev.end_x, ev.end_y, ev.pressure)
                self.last_pass_difficulty[ev.event_id] = diff
                if ev.outcome == "complete" and diff >= 8:
                    ps.elite_passes += 1
                self._momentum(t, team, momentum_points("pass", ev.outcome, progressive=prog))
            case "carry":
                assert ps
                s.possession = team
                ps.carries += 1
                ps.carry_m += ev.distance_m
            case "shot":
                assert ts and ps
                s.possession = team
                ts.shots += 1
                ps.shots += 1
                ts.xg += ev.xg
                ps.xg += ev.xg
                ts.top_shot_speed_kmh = max(ts.top_shot_speed_kmh, ev.speed_kmh)
                ps.top_shot_speed_kmh = max(ps.top_shot_speed_kmh, ev.speed_kmh)
                if ev.outcome in ("goal", "saved"):
                    ts.shots_on_target += 1
                if ev.outcome == "goal":
                    ts.goals += 1
                    ps.goals += 1
                self._momentum(t, team, momentum_points("shot", ev.outcome))
            case "tackle":
                if ev.outcome == "won" and ts and ps:
                    ts.tackles_won += 1
                    ps.tackles_won += 1
                    self._momentum(t, team, momentum_points("tackle", "won", x=ev.x))
            case "interception":
                if ts and ps:
                    ts.interceptions += 1
                    ps.interceptions += 1
            case "pressure":
                if ts:
                    ts.pressures += 1
            case "foul":
                assert ts and ps
                ts.fouls += 1
                if ev.card == "yellow":
                    ts.yellow_cards += 1
                    ps.yellow_cards += 1
                elif ev.card == "red":
                    ts.red_cards += 1
                    ts.players_on_pitch -= 1
                    ps.sent_off = True
            case "possession_change":
                s.possession = ev.to_team
            case "substitution":
                pass
            case "sprint":
                if ps:
                    ps.sprints += 1
                    ps.top_speed_kmh = max(ps.top_speed_kmh, ev.top_speed_kmh)
            case "distance_milestone":
                if ps:
                    ps.distance_km = max(ps.distance_km, ev.total_km)
        return self._samples(t)

    def broadcast_minute(self, t: float) -> float:
        """Continuous seconds -> broadcast minutes (the second half restarts at 45:00)."""
        if self.state.period == 1:
            return round(t / 60, 1)
        return round(45 + (t - self.half1_end) / 60, 1)

    # ------------------------------------------------------------------ internals
    def _advance_clock(self, t: float) -> None:
        """Credit elapsed time to whoever had the ball, and trim the rolling windows."""
        s = self.state
        if s.possession and t > self.last_t and s.status in ("first_half", "second_half"):
            s.teams[s.possession].possession_s += t - self.last_t
            s.possession_window.append((self.last_t, t, s.possession))
        self.last_t = max(self.last_t, t)
        s.t = self.last_t
        lo = s.t - WINDOW_S
        while s.window and s.window[0][0] < lo:
            s.window.popleft()
        while s.pass_window and s.pass_window[0][0] < lo:
            s.pass_window.popleft()
        while s.possession_window and s.possession_window[0][1] < lo:
            s.possession_window.popleft()

    def _momentum(self, t: float, team: str, points: int) -> None:
        if points:
            self.state.window.append((t, team, points))

    def _samples(self, t: float) -> list[float]:
        """Record the momentum and pressure series once per match minute."""
        s = self.state
        crossed: list[float] = []
        while t >= self.next_sample:
            minute = self.broadcast_minute(self.next_sample)
            s.momentum_series.append((minute, s.momentum()))
            for team in s.teams:
                s.pressure_series[team].append((minute, s.pressure_index(team)))
            crossed.append(minute)
            self.next_sample += SAMPLE_EVERY_S
        return crossed
