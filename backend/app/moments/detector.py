"""Moment Detector: rule-based candidate moments with base importance (SPEC section 9.1).

Rules decide *what* is a moment and gather its facts from the Match State. Agents (M3) only decide how
to explain it, and may cite only these facts.
"""

from __future__ import annotations

from typing import Any

from app.moments.models import BASE_SCORE, Moment, MomentType
from app.simulator.schema import MatchEvent
from app.state.match_state import MatchState
from app.stats.engine import StatsEngine

BIG_CHANCE_XG = 0.3
# SPEC 9.1 says difficulty >= 8; the formula saturates at 8 for any long ball into the final third
# (~20 a match), so "elite" is calibrated to 9.5 (~4 a match). See docs/PROGRESS.md.
ELITE_PASS_DIFFICULTY = 9.5
SWING_MIN_DELTA = 40
SWING_MIN_NOW = 25  # the team must now be clearly on top, not just past zero
SWING_LOOKBACK_MIN = 5
SWING_COOLDOWN_MIN = 10
SPIKE_MIN_DELTA = 0.25
SPIKE_COOLDOWN_MIN = 10


class MomentDetector:
    def __init__(self, state: MatchState, stats: StatsEngine):
        self.state = state
        self.stats = stats
        self.n = 0
        self.last_swing = -99.0
        self.last_spike: dict[str, float] = {}
        self.last_completed_pass: dict[str, MatchEvent] = {}  # receiver -> pass

    # ------------------------------------------------------------------ helpers
    def _moment(
        self,
        mtype: MomentType,
        ev: MatchEvent | None,
        facts: dict[str, Any],
        team: str | None = None,
        player: str | None = None,
    ) -> Moment:
        self.n += 1
        s = self.state
        base = {
            "minute": s.minute,
            "match_clock": s.match_clock,
            "score": f"{s.score[0]}-{s.score[1]}",
            "home": s.club_names[s.home_id],
            "away": s.club_names[s.away_id],
        }
        return Moment(
            moment_id=f"{s.match.match_id}-mom-{self.n:04d}",
            type=mtype,
            match_clock=s.match_clock,
            period=s.period,
            minute=s.minute,
            team_id=team,
            player_id=player,
            base_score=BASE_SCORE[mtype],
            facts={**base, **facts},
            event_id=ev.event_id if ev else None,
        )

    def _name(self, pid: str | None) -> str | None:
        return self.state.names.get(pid) if pid else None

    def _team_facts(self, team: str) -> dict[str, Any]:
        s = self.state
        ts, os_ = s.teams[team], s.teams[s.other(team)]
        return {
            "team": s.club_names[team],
            "opponent": s.club_names[s.other(team)],
            "team_xg": round(ts.xg, 2),
            "opponent_xg": round(os_.xg, 2),
            "team_shots": ts.shots,
            "opponent_shots": os_.shots,
        }

    # ------------------------------------------------------------------ per event
    def on_event(self, ev: MatchEvent) -> list[Moment]:
        """Call after the Stats Engine has applied ``ev``."""
        s = self.state
        out: list[Moment] = []
        if ev.type == "pass" and ev.outcome == "complete" and ev.receiver_id:
            self.last_completed_pass[ev.receiver_id] = ev
            diff = self.stats.last_pass_difficulty.get(ev.event_id, 0.0)
            if diff >= ELITE_PASS_DIFFICULTY:
                assert ev.team_id
                out.append(
                    self._moment(
                        "elite_pass",
                        ev,
                        {
                            "player": self._name(ev.player_id),
                            "receiver": self._name(ev.receiver_id),
                            "team": s.club_names[ev.team_id],
                            "difficulty": diff,
                            "distance_m": round(
                                ((ev.end_x - (ev.x or 0)) ** 2 + (ev.end_y - (ev.y or 0)) ** 2) ** 0.5, 1
                            ),
                            "pressure": ev.pressure,
                            "ball_speed_kmh": ev.speed_kmh,
                        },
                        ev.team_id,
                        ev.player_id,
                    )
                )
        elif ev.type == "shot":
            assert ev.team_id and ev.player_id
            facts = {
                "player": self._name(ev.player_id),
                "xg": round(ev.xg, 2),
                "shot_speed_kmh": ev.speed_kmh,
                "outcome": ev.outcome,
                **self._team_facts(ev.team_id),
            }
            if ev.outcome == "goal":
                assist = self.last_completed_pass.get(ev.player_id)
                if assist and assist.team_id == ev.team_id:
                    facts["assist"] = self._name(assist.player_id)
                    facts["assist_difficulty"] = self.stats.last_pass_difficulty.get(assist.event_id)
                facts["player_goals"] = s.players[ev.player_id].goals
                facts["momentum"] = s.momentum() if ev.team_id == s.home_id else -s.momentum()
                out.append(self._moment("goal", ev, facts, ev.team_id, ev.player_id))
            elif ev.xg >= BIG_CHANCE_XG:
                out.append(self._moment("big_chance", ev, facts, ev.team_id, ev.player_id))
        elif ev.type == "foul" and ev.card in ("red", "yellow"):
            assert ev.team_id
            facts = {
                "player": self._name(ev.player_id),
                "team": s.club_names[ev.team_id],
                "team_fouls": s.teams[ev.team_id].fouls,
            }
            if ev.card == "red":
                facts["players_left"] = s.teams[ev.team_id].players_on_pitch
                out.append(self._moment("red_card", ev, facts, ev.team_id, ev.player_id))
            else:
                out.append(self._moment("yellow_card", ev, facts, ev.team_id, ev.player_id))
        elif ev.type in ("half_time", "full_time"):
            out.append(self._period_summary(ev))
        return out

    def _period_summary(self, ev: MatchEvent) -> Moment:
        s = self.state
        h, a = s.team_snapshot(s.home_id), s.team_snapshot(s.away_id)
        ranked = sorted(
            s.players.items(),
            key=lambda kv: kv[1].goals * 3 + kv[1].xg * 2 + kv[1].elite_passes + kv[1].tackles_won * 0.3,
            reverse=True,
        )
        facts = {
            "home_xg": h["xg"],
            "away_xg": a["xg"],
            "home_shots": h["shots"],
            "away_shots": a["shots"],
            "home_possession": h["possession"],
            "away_possession": a["possession"],
            "home_pass_accuracy": h["pass_accuracy"],
            "away_pass_accuracy": a["pass_accuracy"],
            "top_performer": s.names[ranked[0][0]],
            "goals": [
                {"minute": m.minute, "player": m.facts["player"], "team": m.facts["team"]}
                for m in s.moments
                if m.type == "goal"
            ],
        }
        return self._moment("half_time" if ev.type == "half_time" else "full_time", ev, facts)

    # ------------------------------------------------------------------ per minute
    def on_sample(self, minute: float) -> list[Moment]:
        """Rolling checks, run once per match minute after the series are sampled."""
        s = self.state
        out: list[Moment] = []
        series = s.momentum_series
        if len(series) > SWING_LOOKBACK_MIN and minute - self.last_swing >= SWING_COOLDOWN_MIN:
            now = series[-1][1]
            before = series[-1 - SWING_LOOKBACK_MIN][1]
            if now * before < 0 and abs(now - before) >= SWING_MIN_DELTA and abs(now) >= SWING_MIN_NOW:
                team = s.home_id if now > 0 else s.away_id
                self.last_swing = minute
                out.append(
                    self._moment(
                        "momentum_swing",
                        None,
                        {
                            "momentum_now": abs(now),
                            "momentum_5min_ago": abs(before),
                            "swing": abs(now - before),
                            **self._team_facts(team),
                        },
                        team,
                    )
                )
        for team, pseries in s.pressure_series.items():
            if (
                len(pseries) <= SWING_LOOKBACK_MIN
                or minute - self.last_spike.get(team, -99) < SPIKE_COOLDOWN_MIN
            ):
                continue
            now_p, before_p = pseries[-1][1], pseries[-1 - SWING_LOOKBACK_MIN][1]
            if now_p is None or before_p is None or now_p - before_p < SPIKE_MIN_DELTA:
                continue
            self.last_spike[team] = minute
            out.append(
                self._moment(
                    "pressure_spike",
                    None,
                    {
                        "pressed_team": s.club_names[team],
                        "pressing_team": s.club_names[s.other(team)],
                        "pressure_index": now_p,
                        "pressure_index_5min_ago": before_p,
                        "pressing_team_pressures": s.teams[s.other(team)].pressures,
                    },
                    s.other(team),
                )
            )
        return out


class MatchAnalyzer:
    """Stats Engine + Moment Detector over one match: feed events, get moments."""

    def __init__(self, state: MatchState):
        self.state = state
        self.stats = StatsEngine(state)
        self.detector = MomentDetector(state, self.stats)

    def feed(self, ev: MatchEvent) -> list[Moment]:
        samples = self.stats.apply(ev)
        moments: list[Moment] = []
        for minute in samples:
            moments.extend(self.detector.on_sample(minute))
        moments.extend(self.detector.on_event(ev))
        self.state.moments.extend(moments)
        return moments
