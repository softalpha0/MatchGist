"""Key-moment detection: turns raw events and state into ``Insight``s.

Detection is deterministic on purpose: it decides *what* matters and gathers
the facts. Language agents only decide *how to say why*, and may cite only
the facts gathered here.
"""

from __future__ import annotations

from touchline.analytics.state import MatchState
from touchline.models import EventType, Insight, InsightKind, MatchEvent, Side

SPRINT_TAG_SPEED = 8.0  # m/s (28.8 km/h): threshold for an on-screen speed tag
ROCKET_SHOT_KMH = 100.0
MILESTONE_PASSES = (50, 100)
MILESTONE_KM = (10.0,)


def clock_label(period: int, minute: float) -> str:
    """Broadcast-style clock: 23', 45+2', 90+4'."""
    m = int(minute) + 1
    cap = 45 if period == 1 else 90
    return f"{cap}+{m - cap}'" if m > cap else f"{m}'"


class MomentDetector:
    def __init__(self, state: MatchState):
        self.state = state
        self.n = 0
        self.momentum_regime = 0  # -1 away, 0 even, +1 home
        self.chaos_regime = 0  # -1 control, 0 neutral, +1 chaos
        self.pressure_last: dict[Side, float] = {Side.HOME: 0.0, Side.AWAY: 0.0}
        self.next_index_check = 120.0
        self.last_kind_t: dict[str, float] = {}
        self.sprint_cooldown: dict[str, float] = {}
        self.fastest = 0.0
        self.milestones: set[tuple[str, str]] = set()

    def _id(self) -> str:
        self.n += 1
        return f"{self.state.meta.match_id}-i{self.n}"

    def _name(self, pid: str | None) -> str | None:
        return self.state.player_name.get(pid) if pid else None

    def _club(self, side: Side | None) -> str | None:
        if side is None:
            return None
        return (self.state.meta.home if side is Side.HOME else self.state.meta.away).name

    def _base_facts(self, side: Side | None = None, pid: str | None = None) -> dict:
        f: dict = {
            "minute": clock_label(self.state.period, self.state.minute),
            "score": list(self.state.score),
        }
        if side is not None:
            f["team"] = self._club(side)
            f["opponent"] = self._club(side.other)
        if pid:
            f["player"] = self._name(pid)
        return f

    def _last_pass_to(self, pid: str, before_seq: int) -> MatchEvent | None:
        for e in reversed(self.state.recent):
            if e.seq >= before_seq:
                continue
            if e.type is EventType.PASS:
                return e if e.target_id == pid and e.outcome == "complete" else None
            if e.type in (EventType.POSSESSION_CHANGE, EventType.SHOT):
                return None
        return None

    # ---------------------------------------------------------------- events
    def on_event(self, ev: MatchEvent) -> list[Insight]:
        out = self._on_event(ev)
        geo = {k: v for k in ("x", "y", "end_x", "end_y") if (v := getattr(ev, k)) is not None}
        for ins in out:
            if ev.id in ins.event_ids:
                ins.geo = geo
        return out

    def _on_event(self, ev: MatchEvent) -> list[Insight]:
        s = self.state
        out: list[Insight] = []
        if ev.type is EventType.GOAL:
            side = ev.side
            assert side is not None
            facts = self._base_facts(side, ev.player_id)
            mom = s.momentum()
            facts.update(
                {
                    "xg": ev.data.get("xg"),
                    "shot_speed_kmh": ev.data.get("speed_kmh"),
                    "distance_m": ev.data.get("distance"),
                    "team_xg": round(s.team[side].xg, 2),
                    "opponent_xg": round(s.team[side.other].xg, 2),
                    "momentum_for_team": round(mom if side is Side.HOME else -mom, 2),
                    "player_goals": s.players[ev.player_id].goals if ev.player_id else None,
                }
            )
            shot_seq = int(str(ev.data.get("shot_id", "0")).rsplit("-", 1)[-1] or 0)
            assist = self._last_pass_to(ev.player_id or "", shot_seq)
            if assist and assist.player_id:
                facts["assist"] = self._name(assist.player_id)
                facts["assist_difficulty"] = round(10 * float(assist.data.get("difficulty", 0)), 1)
            facts["against_run_of_play"] = facts["momentum_for_team"] < -0.25
            facts["low_xg_finish"] = (ev.data.get("xg") or 1) < 0.08
            out.append(
                Insight(
                    id=self._id(),
                    t=ev.t,
                    kind="goal",
                    side=side,
                    player_id=ev.player_id,
                    importance=1.0,
                    facts=facts,
                    event_ids=[ev.id],
                )
            )
        elif ev.type is EventType.SHOT and ev.outcome != "goal":
            xg = float(ev.data.get("xg", 0))
            kmh = float(ev.data.get("speed_kmh", 0))
            facts = self._base_facts(ev.side, ev.player_id)
            facts.update(
                {
                    "xg": round(xg, 2),
                    "outcome": ev.outcome,
                    "shot_speed_kmh": kmh,
                    "distance_m": ev.data.get("distance"),
                }
            )
            if xg >= 0.25:
                out.append(
                    Insight(
                        id=self._id(),
                        t=ev.t,
                        kind="big_chance",
                        side=ev.side,
                        player_id=ev.player_id,
                        importance=0.75,
                        facts=facts,
                        event_ids=[ev.id],
                    )
                )
            elif kmh >= ROCKET_SHOT_KMH or ev.outcome == "saved":
                out.append(
                    Insight(
                        id=self._id(),
                        t=ev.t,
                        kind="shot",
                        side=ev.side,
                        player_id=ev.player_id,
                        importance=0.45,
                        facts=facts,
                        event_ids=[ev.id],
                    )
                )
        elif ev.type is EventType.PASS and ev.outcome == "complete":
            diff = float(ev.data.get("difficulty", 0))
            length = float(ev.data.get("length", 0))
            if (diff >= 0.42 and ev.data.get("progressive")) or (length >= 40 and diff >= 0.3):
                facts = self._base_facts(ev.side, ev.player_id)
                facts.update(
                    {
                        "receiver": self._name(ev.target_id),
                        "length_m": length,
                        "ball_speed_kmh": round(3.6 * float(ev.data.get("speed", 0)), 1),
                        "difficulty": round(10 * diff, 1),
                        "completion_chance": round(100 * float(ev.data.get("x_completion", 0))),
                        "accuracy": round(100 * float(ev.data.get("accuracy", 0))),
                        "under_pressure": bool(ev.data.get("pressured")),
                    }
                )
                out.append(
                    Insight(
                        id=self._id(),
                        t=ev.t,
                        kind="pass_of_note",
                        side=ev.side,
                        player_id=ev.player_id,
                        importance=0.45,
                        facts=facts,
                        event_ids=[ev.id],
                    )
                )
            out.extend(self._pass_milestone(ev))
        elif ev.type is EventType.CARD:
            facts = self._base_facts(ev.side, ev.player_id)
            facts["card"] = ev.outcome
            facts["team_fouls"] = s.team[ev.side].fouls if ev.side else None
            out.append(
                Insight(
                    id=self._id(),
                    t=ev.t,
                    kind="card",
                    side=ev.side,
                    player_id=ev.player_id,
                    importance=0.5,
                    facts=facts,
                    event_ids=[ev.id],
                )
            )
        elif ev.type in (EventType.HALF_TIME, EventType.FULL_TIME):
            out.append(self._period_summary(ev))
        return out

    def _pass_milestone(self, ev: MatchEvent) -> list[Insight]:
        pid = ev.player_id
        if not pid:
            return []
        n = self.state.players[pid].passes_completed
        if n in MILESTONE_PASSES and (pid, f"p{n}") not in self.milestones:
            self.milestones.add((pid, f"p{n}"))
            ps = self.state.players[pid]
            facts = self._base_facts(ev.side, pid)
            facts.update(
                {
                    "milestone": "completed_passes",
                    "value": n,
                    "pass_accuracy": round(100 * ps.passes_completed / max(ps.passes, 1)),
                }
            )
            return [
                Insight(
                    id=self._id(),
                    t=ev.t,
                    kind="milestone",
                    side=ev.side,
                    player_id=pid,
                    importance=0.3 + 0.002 * n,
                    facts=facts,
                    event_ids=[ev.id],
                )
            ]
        return []

    def _period_summary(self, ev: MatchEvent) -> Insight:
        s = self.state
        snap = s.snapshot()
        top = sorted(
            s.players.items(),
            key=lambda kv: (
                kv[1].goals * 3 + kv[1].xg * 2 + kv[1].progressive_passes * 0.1 + kv[1].tackles_won * 0.2
            ),
            reverse=True,
        )[:3]
        facts = {
            "minute": "HT" if ev.type is EventType.HALF_TIME else "FT",
            "score": list(s.score),
            "home": s.meta.home.name,
            "away": s.meta.away.name,
            "home_xg": snap["home"]["xg"],
            "away_xg": snap["away"]["xg"],
            "home_possession": snap["home"]["possession"],
            "away_possession": snap["away"]["possession"],
            "home_shots": snap["home"]["shots"],
            "away_shots": snap["away"]["shots"],
            "standout": [s.player_name[pid] for pid, _ in top],
            "goals": [
                {
                    "minute": clock_label(int(e.data.get("period", 1)), float(e.data.get("minute", 0))),
                    "player": self._name(e.player_id),
                    "team": self._club(e.side),
                }
                for e in s.recent
                if e.type is EventType.GOAL
            ],
        }
        kind: InsightKind = "half_time" if ev.type is EventType.HALF_TIME else "full_time"
        return Insight(id=self._id(), t=ev.t, kind=kind, importance=1.0, facts=facts, event_ids=[ev.id])

    # ---------------------------------------------------------------- tracking
    def on_sprints(self, started: list[tuple[str, float]], t: float) -> list[Insight]:
        out: list[Insight] = []
        for pid, speed in started:
            ps = self.state.players[pid]
            if speed < SPRINT_TAG_SPEED or t < self.sprint_cooldown.get(pid, 0):
                continue
            self.sprint_cooldown[pid] = t + 90
            fastest = speed > self.fastest and t > 600  # "fastest so far" means little in minute 2
            self.fastest = max(self.fastest, speed)
            side = self.state.player_side[pid]
            facts = self._base_facts(side, pid)
            facts.update(
                {
                    "speed_kmh": round(speed * 3.6, 1),
                    "top_speed_kmh": round(ps.top_speed * 3.6, 1),
                    "sprints": ps.sprints,
                    "distance_km": round(ps.distance / 1000, 2),
                    "fastest_in_match": fastest,
                }
            )
            out.append(
                Insight(
                    id=self._id(),
                    t=t,
                    kind="sprint",
                    side=side,
                    player_id=pid,
                    importance=0.3 + (0.15 if fastest else 0),
                    facts=facts,
                )
            )
        for pid, ps in self.state.players.items():
            for km in MILESTONE_KM:
                key = (pid, f"km{km}")
                if ps.distance >= km * 1000 and key not in self.milestones:
                    self.milestones.add(key)
                    side = self.state.player_side[pid]
                    facts = self._base_facts(side, pid)
                    facts.update({"milestone": "distance_km", "value": km, "sprints": ps.sprints})
                    out.append(
                        Insight(
                            id=self._id(),
                            t=t,
                            kind="milestone",
                            side=side,
                            player_id=pid,
                            importance=0.25,
                            facts=facts,
                        )
                    )
        return out

    # ---------------------------------------------------------------- indices
    def _gap_ok(self, key: str, t: float, gap: float) -> bool:
        if t - self.last_kind_t.get(key, -1e9) < gap:
            return False
        self.last_kind_t[key] = t
        return True

    def on_clock(self, t: float) -> list[Insight]:
        """Periodic checks of rolling indices (every 30 s of match time)."""
        if t < self.next_index_check:
            return []
        self.next_index_check = t + 30
        s = self.state
        out: list[Insight] = []

        mom = s.momentum()
        regime = 1 if mom > 0.35 else -1 if mom < -0.35 else self.momentum_regime if abs(mom) > 0.15 else 0
        if regime != 0 and regime != self.momentum_regime and self._gap_ok("momentum_swing", t, 240):
            side = Side.HOME if regime > 0 else Side.AWAY
            ts, os_ = s.team[side], s.team[side.other]
            window = s.window_events()
            facts = self._base_facts(side)
            facts.update(
                {
                    "momentum": round(abs(mom), 2),
                    "window_minutes": 5,
                    "shots_in_window": sum(1 for e in window if e.type is EventType.SHOT and e.side is side),
                    "opponent_shots_in_window": sum(
                        1 for e in window if e.type is EventType.SHOT and e.side is side.other
                    ),
                    "final_third_passes_in_window": sum(
                        1
                        for e in window
                        if e.type is EventType.PASS
                        and e.side is side
                        and e.outcome == "complete"
                        and e.end_x is not None
                        and s._in_final_third(side, e.end_x)
                    ),
                    "team_xg": round(ts.xg, 2),
                    "opponent_xg": round(os_.xg, 2),
                    "trailing": s.score[0 if side is Side.HOME else 1]
                    < s.score[1 if side is Side.HOME else 0],
                }
            )
            out.append(
                Insight(id=self._id(), t=t, kind="momentum_swing", side=side, importance=0.6, facts=facts)
            )
        self.momentum_regime = regime
        s.momentum_series.append((t, mom))

        ctl = s.control()
        chaos = ctl["chaos"]
        if chaos >= 62:
            c_regime = 1
        elif chaos <= 38:
            c_regime = -1
        elif 45 <= chaos <= 55:
            c_regime = 0
        else:
            c_regime = self.chaos_regime
        if c_regime != 0 and c_regime != self.chaos_regime and self._gap_ok("control_shift", t, 480):
            facts = self._base_facts()
            facts.update({"state": "chaos" if c_regime > 0 else "control", **ctl})
            leader = None
            if c_regime < 0:
                passes = {
                    sd: sum(1 for e in s.window_events(180) if e.type is EventType.PASS and e.side is sd)
                    for sd in Side
                }
                leader = max(passes, key=lambda k: passes[k])
                facts["team"] = self._club(leader)
            out.append(
                Insight(id=self._id(), t=t, kind="control_shift", side=leader, importance=0.5, facts=facts)
            )
        self.chaos_regime = c_regime
        s.control_series.append((t, chaos))

        for side in Side:
            p = s.pressure_index(side, 120)
            prev = self.pressure_last[side]
            if p >= 8 and p >= prev * 1.5 and prev > 0 and self._gap_ok(f"pressure_{side}", t, 360):
                facts = self._base_facts(side)
                facts.update(
                    {
                        "pressures_per_min": p,
                        "previous_per_min": prev,
                        "turnovers_forced": sum(
                            1
                            for e in s.window_events(120)
                            if e.type is EventType.POSSESSION_CHANGE and e.side is side
                        ),
                    }
                )
                out.append(
                    Insight(id=self._id(), t=t, kind="pressure_spike", side=side, importance=0.5, facts=facts)
                )
            self.pressure_last[side] = p
        return out
