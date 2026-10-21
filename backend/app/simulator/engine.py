"""Seeded, football-realistic match simulator (SPEC section 8.3).

A possession-chain model on top of light physics. Twenty-two players move toward tactical targets with
speed and acceleration limits. The ball holder chooses to pass, carry or shoot. Outcomes depend on
player ratings and on where the opponents are:

* pass success follows an expected-completion model (distance, passing lane, pressure, passing rating);
* shots use a distance/angle xG model, and shot speed depends on the shooting rating;
* tackles depend on the defending rating against the carrier's pace.

Everything flows from one ``random.Random(seed)``, so the same seed always produces the same match.
"""

from __future__ import annotations

import asyncio
import json
import math
import random
import time
from collections.abc import AsyncIterator, Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.config import DATA_DIR
from app.simulator.schema import (
    PITCH_LENGTH,
    PITCH_WIDTH,
    Club,
    Match,
    MatchEvent,
    PlayerRecord,
    Storyline,
    parse_event,
)
from app.simulator.storylines import AWAY, HOME, StoryPlan, plan_for, satisfied

DT = 0.5  # simulation step, seconds
HALF = 45 * 60
GOAL_HALF_WIDTH = 3.66
VENUES = ["Lantern Park", "The Saltworks", "Millbrook Stadium", "Copperfield Ground"]
MAX_STORY_ATTEMPTS = 60

# How much a passer prefers each role as receiver, by the third of the pitch the passer is in:
# build through defence and midfield, look for forwards once in the final third.
ROLE_RECEIVE_BIAS = {
    "own": {"GK": 0.0, "DF": 1.1, "MF": 0.9, "FW": 0.0},
    "middle": {"GK": 0.0, "DF": 0.9, "MF": 0.8, "FW": 0.5},
    "final": {"GK": 0.0, "DF": 0.2, "MF": 0.7, "FW": 0.9},
}

# 4-3-3 slots: (position, x as share of the pitch from own goal, y as share of the width)
FORMATION: list[tuple[str, float, float]] = [
    ("GK", 0.04, 0.50),
    ("DF", 0.22, 0.15),
    ("DF", 0.20, 0.38),
    ("DF", 0.20, 0.62),
    ("DF", 0.22, 0.85),
    ("MF", 0.42, 0.30),
    ("MF", 0.38, 0.50),
    ("MF", 0.42, 0.70),
    ("FW", 0.62, 0.18),
    ("FW", 0.66, 0.50),
    ("FW", 0.62, 0.82),
]


def load_clubs(path: Path | None = None) -> dict[str, Club]:
    raw = json.loads((path or DATA_DIR / "clubs.json").read_text(encoding="utf-8"))
    clubs = [Club.model_validate(c) for c in raw["clubs"]]
    return {c.club_id: c for c in clubs}


def clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v


def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def point_segment_distance(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    seg = dx * dx + dy * dy
    if seg == 0:
        return dist(p, a)
    u = clamp(((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / seg, 0.0, 1.0)
    return dist(p, (a[0] + u * dx, a[1] + u * dy))


def expected_goals(distance: float, angle: float, pressured: bool, header: bool) -> float:
    """Logistic xG from distance (m) and the visible goal-mouth angle (rad)."""
    logit = -1.1 - 0.12 * distance + 1.6 * angle - (0.6 if pressured else 0) - (0.7 if header else 0)
    return 1.0 / (1.0 + math.exp(-logit))


def goal_angle(x: float, y: float, goal_x: float) -> float:
    a = math.atan2(PITCH_WIDTH / 2 + GOAL_HALF_WIDTH - y, abs(goal_x - x))
    b = math.atan2(PITCH_WIDTH / 2 - GOAL_HALF_WIDTH - y, abs(goal_x - x))
    return abs(a - b)


def pressure_from_distance(d: float) -> float:
    """0 when the nearest opponent is 5 m or more away, 1 when they are on top of the player."""
    return round(clamp(1 - (d - 0.5) / 4.5, 0.0, 1.0), 2)


@dataclass
class Flight:
    kind: str  # pass | cross | shot
    passer: str
    receiver: str | None
    start: tuple[float, float]
    end: tuple[float, float]
    t0: float
    t1: float
    speed: float
    success: bool
    interceptor: str | None
    pressure: float
    data: dict[str, Any] = field(default_factory=dict)
    out_of_play: bool = False


@dataclass
class DeadBall:
    resume_t: float
    side: str
    taker: str
    spot: tuple[float, float]
    kind: str  # kick_off | free_kick | goal_kick | corner | throw_in
    reset_shape: bool = False


class MatchEngine:
    """Simulates one match. Use :func:`generate_match` rather than this class directly."""

    def __init__(self, seed: int, home: Club, away: Club, plan: StoryPlan, match_id: str):
        self.rng = random.Random(seed)
        self.plan = plan
        self.match_id = match_id
        self.clubs = {HOME: home, AWAY: away}
        self.records: dict[str, PlayerRecord] = {p.player_id: p for c in (home, away) for p in c.players}
        self.side: dict[str, str] = {p.player_id: s for s, c in self.clubs.items() for p in c.players}
        self.on_pitch: dict[str, list[str]] = {}
        self.slot: dict[str, int] = {}
        for s, club in self.clubs.items():
            xi = self._line_up(club.starters())
            self.on_pitch[s] = xi
            for i, pid in enumerate(xi):
                self.slot[pid] = i
        self.bench = {s: [p.player_id for p in c.bench()] for s, c in self.clubs.items()}
        self.sub_minutes = {s: sorted(self.rng.uniform(55, 86) for _ in range(3)) for s in (HOME, AWAY)}
        self.pos: dict[str, list[float]] = {}
        self.vel: dict[str, list[float]] = {pid: [0.0, 0.0] for pid in self.records}
        self.ran: dict[str, float] = {pid: 0.0 for pid in self.records}
        self.phase = {pid: self.rng.uniform(0, math.tau) for pid in self.records}
        self.stoppage = (self.rng.randint(1, 3) * 60, self.rng.randint(2, 5) * 60)
        self.t = 0.0
        self.period = 1
        self.period_start = 0.0
        self.seq = 0
        self.score = {HOME: 0, AWAY: 0}
        self.yellows: set[str] = set()
        self.sent_off: set[str] = set()
        self.holder: str | None = None
        self.flight: Flight | None = None
        self.dead: DeadBall | None = None
        self.ball = [PITCH_LENGTH / 2, PITCH_WIDTH / 2]
        self.ball_smooth = [PITCH_LENGTH / 2, PITCH_WIDTH / 2]
        self.next_action_t = 0.0
        self.carry_target: tuple[float, float] | None = None
        self.carry_start: tuple[float, float, float] | None = None
        self.tackle_cooldown: dict[str, float] = {}
        self.spell_start_gap = 0.0
        self.pressing = False
        self.pressed_this_spell = False
        self.possession = HOME
        self.events: list[dict[str, Any]] = []
        self.finished = False

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _line_up(starters: list[PlayerRecord]) -> list[str]:
        """Order the XI to match FORMATION slots by position."""
        by_pos: dict[str, list[str]] = {"GK": [], "DF": [], "MF": [], "FW": []}
        for p in starters:
            by_pos[p.position].append(p.player_id)
        out: list[str] = []
        for pos, _, _ in FORMATION:
            pool = by_pos[pos] or next(v for v in by_pos.values() if v)
            out.append(pool.pop(0))
        return out

    def rating(self, pid: str, attr: str) -> float:
        return getattr(self.records[pid], attr) / 100.0

    def position(self, pid: str) -> str:
        return self.records[pid].position

    def direction(self, side: str) -> int:
        """+1 if ``side`` attacks toward x=105 (absolute frame) in the current period."""
        base = 1 if side == HOME else -1
        return base if self.period == 1 else -base

    def goal_x(self, side: str) -> float:
        return PITCH_LENGTH if self.direction(side) == 1 else 0.0

    def minute(self) -> float:
        return (0.0 if self.period == 1 else 45.0) + (self.t - self.period_start) / 60.0

    def clock(self) -> str:
        secs = int(self.t - self.period_start) + (0 if self.period == 1 else HALF)
        return f"{secs // 60:02d}:{secs % 60:02d}"

    def rel(self, side: str, x: float, y: float) -> tuple[float, float]:
        """Absolute -> team-relative coordinates (``side`` attacks toward x=105)."""
        if self.direction(side) == 1:
            return round(clamp(x, 0, PITCH_LENGTH), 1), round(clamp(y, 0, PITCH_WIDTH), 1)
        return round(clamp(PITCH_LENGTH - x, 0, PITCH_LENGTH), 1), round(
            clamp(PITCH_WIDTH - y, 0, PITCH_WIDTH), 1
        )

    def team_id(self, side: str) -> str:
        return self.clubs[side].club_id

    def _p(self, pid: str) -> tuple[float, float]:
        return (self.pos[pid][0], self.pos[pid][1])

    def nearest_opponent(self, pid: str) -> tuple[str, float]:
        me = self._p(pid)
        best, bd = "", 1e9
        for oid in self.on_pitch[self._other(self.side[pid])]:
            d = dist(me, self._p(oid))
            if d < bd:
                best, bd = oid, d
        return best, bd

    @staticmethod
    def _other(side: str) -> str:
        return AWAY if side == HOME else HOME

    def _emit(
        self,
        etype: str,
        side: str | None = None,
        pid: str | None = None,
        xy: tuple[float, float] | None = None,
        **fields: Any,
    ) -> dict[str, Any]:
        self.seq += 1
        ev: dict[str, Any] = {
            "event_id": f"{self.match_id}-{self.seq:06d}",
            "match_id": self.match_id,
            "seq": self.seq,
            "match_clock": self.clock(),
            "period": self.period,
            "type": etype,
            "team_id": self.team_id(side) if side else None,
            "player_id": pid,
            "x": None,
            "y": None,
            "meta": fields.pop("meta", {}),
        }
        if xy is not None and side is not None:
            ev["x"], ev["y"] = self.rel(side, *xy)
        ev.update(fields)
        self.events.append(ev)
        return ev

    def _set_possession(self, side: str, cause: str, at: tuple[float, float]) -> None:
        if side != self.possession:
            self._emit(
                "possession_change",
                side,
                self.holder,
                at,
                from_team=self.team_id(self.possession),
                to_team=self.team_id(side),
                cause=cause,
            )
            self.possession = side

    def _give_ball(self, pid: str, cause: str, delay: tuple[float, float] = (3.2, 6.2)) -> None:
        self.holder = pid
        self.spell_start_gap = self.nearest_opponent(pid)[1]
        self.pressing = self.rng.random() < self._press_probability(self._other(self.side[pid]), pid)
        self.pressed_this_spell = False
        self._set_possession(self.side[pid], cause, self._p(pid))
        self.flight = None
        self.carry_target = None
        self.carry_start = None
        self.next_action_t = self.t + self.rng.uniform(*delay)

    def _press_probability(self, defending: str, carrier: str) -> float:
        """Chance the defending side presses this spell: style plus how close the ball is to their goal."""
        base = {"pressing": 0.24, "balanced": 0.14, "direct": 0.12, "possession": 0.17}[
            self.clubs[defending].style
        ]
        own_goal_x = 0.0 if self.direction(defending) == 1 else PITCH_LENGTH
        gap = abs(self.pos[carrier][0] - own_goal_x)
        if gap < 30:
            base += 0.45  # nobody lets a forward turn freely at the edge of the box
        elif gap < 45:
            base += 0.12
        return base

    def _place_for_kickoff(self, kicking: str) -> str:
        for side, ids in self.on_pitch.items():
            d = self.direction(side)
            for pid in ids:
                _, fx, fy = FORMATION[self.slot[pid]]
                rel = clamp(fx * 0.75, 0.02, 0.47)
                self.pos[pid] = [PITCH_LENGTH / 2 - d * (0.5 - rel) * PITCH_LENGTH, fy * PITCH_WIDTH]
                self.vel[pid] = [0.0, 0.0]
        taker = self._kickoff_taker(kicking)
        self.pos[taker] = [PITCH_LENGTH / 2, PITCH_WIDTH / 2]
        self.ball = [PITCH_LENGTH / 2, PITCH_WIDTH / 2]
        return taker

    def _kickoff_taker(self, side: str) -> str:
        for pos in ("FW", "MF", "DF"):
            for pid in self.on_pitch[side]:
                if self.position(pid) == pos:
                    return pid
        return self.on_pitch[side][0]

    # ------------------------------------------------------------------ main loop
    def run(self) -> list[dict[str, Any]]:
        taker = self._place_for_kickoff(HOME)
        self._emit(
            "kickoff",
            HOME,
            taker,
            self._p(taker),
            meta={"home": self.clubs[HOME].name, "away": self.clubs[AWAY].name},
        )
        self.holder = taker
        self.next_action_t = 0.5
        while not self.finished:
            self.t += DT
            self._step()
        return self.events

    def _step(self) -> None:
        if self.t - self.period_start >= HALF + self.stoppage[self.period - 1] and self.flight is None:
            self._end_period()
            return
        self._substitutions()
        if self.dead is not None:
            self._move_players(reset=self.dead.reset_shape)
            if self.t >= self.dead.resume_t:
                self._resume()
            return
        if self.flight is not None:
            self._advance_flight()
        elif self.holder is not None:
            self._holder_logic()
        self._move_players()
        if self.holder is not None:
            d = self.direction(self.side[self.holder])
            self.ball = [self.pos[self.holder][0] + 0.6 * d, self.pos[self.holder][1]]
            self._pressure_events()

    def _end_period(self) -> None:
        if self.period == 1:
            self._emit("half_time", meta={"score": [self.score[HOME], self.score[AWAY]]})
            self.period = 2
            self.period_start = self.t
            self.flight = None
            self.dead = None
            taker = self._place_for_kickoff(AWAY)
            self._emit("kickoff", AWAY, taker, self._p(taker), meta={"second_half": True})
            self.holder = None
            self._give_ball(taker, "half_time", delay=(0.5, 0.5))
        else:
            self._emit("full_time", meta={"score": [self.score[HOME], self.score[AWAY]]})
            self.finished = True

    # ------------------------------------------------------------------ substitutions and cards
    def _substitutions(self) -> None:
        minute = self.minute()
        for side in (HOME, AWAY):
            plan = self.sub_minutes[side]
            if not plan or minute < plan[0] or not self.bench[side]:
                continue
            # wait for a stoppage, but don't wait more than three minutes
            if self.dead is None and minute < plan[0] + 3:
                continue
            on_id = self._pick_bench(side)
            if on_id is None:
                plan.pop(0)
                continue
            pos = self.position(on_id)
            candidates = [p for p in self.on_pitch[side] if self.position(p) == pos and p != self.holder] or [
                p for p in self.on_pitch[side] if self.position(p) != "GK" and p != self.holder
            ]
            if not candidates:
                continue
            off_id = max(candidates, key=lambda p: self.ran[p])
            plan.pop(0)
            self.bench[side].remove(on_id)
            i = self.on_pitch[side].index(off_id)
            self.on_pitch[side][i] = on_id
            self.slot[on_id] = self.slot[off_id]
            self.pos[on_id] = list(self.pos[off_id])
            self._emit("substitution", side, on_id, self._p(on_id), player_off=off_id, player_on=on_id)

    def _pick_bench(self, side: str) -> str | None:
        outfield = [p for p in self.bench[side] if self.position(p) != "GK"]
        return self.rng.choice(outfield) if outfield else None

    def _book(self, pid: str, forced_red: bool) -> str:
        if forced_red:
            card = "red"
        elif self.rng.random() < (0.05 if pid in self.yellows else 0.16):  # booked players tread carefully
            card = "red" if pid in self.yellows else "yellow"
            self.yellows.add(pid)
        else:
            card = "none"
        if card == "red":
            side = self.side[pid]
            self.sent_off.add(pid)
            self.on_pitch[side].remove(pid)
            self.pos.pop(pid, None)
            if forced_red:
                self.plan.red_side = None
        return card

    # ------------------------------------------------------------------ movement
    def _targets(self, reset: bool) -> dict[str, tuple[float, float, bool]]:
        bx, by = self.ball_smooth
        out: dict[str, tuple[float, float, bool]] = {}
        for side, ids in self.on_pitch.items():
            d = self.direction(side)
            own_goal = 0.0 if d == 1 else PITCH_LENGTH
            ball_rel = (bx - own_goal) * d / PITCH_LENGTH
            attacking = side == self.possession
            for pid in ids:
                pos, fx, fy = FORMATION[self.slot[pid]]
                if pos == "GK":
                    rel = clamp(0.02 + 0.1 * ball_rel, 0.01, 0.12)
                    ty = PITCH_WIDTH / 2 + (by - PITCH_WIDTH / 2) * 0.2
                else:
                    push = (0.10 if attacking else -0.04) + (0.06 if attacking and pos == "FW" else 0)
                    rel = fx + (ball_rel - 0.5) * 0.6 + push
                    if reset:
                        rel = min(rel * 0.75, 0.47)
                    rel = clamp(rel, 0.03, 0.86 if pos == "FW" else 0.8)
                    width = 0.95 if attacking else 0.7
                    ty = (
                        PITCH_WIDTH / 2
                        + (fy * PITCH_WIDTH - PITCH_WIDTH / 2) * width
                        + (by - PITCH_WIDTH / 2) * 0.25
                    )
                ph = self.phase[pid] + self.t * 0.15
                tx = own_goal + d * rel * PITCH_LENGTH + 2.5 * math.sin(ph)
                ty += 2.0 * math.cos(ph * 1.3)
                out[pid] = (clamp(tx, 0.5, PITCH_LENGTH - 0.5), clamp(ty, 0.5, PITCH_WIDTH - 0.5), False)
        if reset or self.dead is not None:
            return out
        bx, by = self.ball
        ball = (bx, by)
        defending = self._other(self.possession)
        chasers = sorted(
            (p for p in self.on_pitch[defending] if self.position(p) != "GK"),
            key=lambda p: dist(self._p(p), ball),
        )[:2]
        if chasers and self.pressing:
            out[chasers[0]] = (bx, by, dist(self._p(chasers[0]), ball) < 12)
        elif chasers:
            # jockey: hold a goal-side position about 4 m off the ball instead of diving in
            gx = 0.0 if self.direction(defending) == 1 else PITCH_LENGTH
            k = 4.0 / max(dist(ball, (gx, PITCH_WIDTH / 2)), 4.0)
            out[chasers[0]] = (bx + (gx - bx) * k, by + (PITCH_WIDTH / 2 - by) * k, False)
        if len(chasers) > 1:
            gx = 0.0 if self.direction(defending) == 1 else PITCH_LENGTH
            out[chasers[1]] = ((bx + gx) / 2 * 0.3 + bx * 0.7, by, False)
        if self.flight is not None and self.flight.receiver:
            r = self.flight.interceptor or self.flight.receiver
            if r in out:
                out[r] = (self.flight.end[0], self.flight.end[1], True)
        if self.holder is not None and self.holder in out:
            if self.carry_target is not None:
                out[self.holder] = (self.carry_target[0], self.carry_target[1], True)
            else:
                hx, hy = self._p(self.holder)
                out[self.holder] = (hx, hy, False)
        return out

    def _move_players(self, reset: bool = False) -> None:
        k = DT / 2.5
        self.ball_smooth[0] += (self.ball[0] - self.ball_smooth[0]) * k
        self.ball_smooth[1] += (self.ball[1] - self.ball_smooth[1]) * k
        for pid, (tx, ty, urgent) in self._targets(reset).items():
            p, v = self.pos[pid], self.vel[pid]
            dx, dy = tx - p[0], ty - p[1]
            d = math.hypot(dx, dy)
            pace = clamp(self.rating(pid, "pace"), 0.2, 1.0)
            vmax = (6.6 + 2.6 * pace) if urgent else min(1.0 + 0.16 * d, 5.0)
            if pid == self.holder:
                vmax = min(vmax, 5.5 + 2.0 * pace)
            desired = (dx / d * min(vmax, d / DT), dy / d * min(vmax, d / DT)) if d > 0.05 else (0.0, 0.0)
            ax, ay = desired[0] - v[0], desired[1] - v[1]
            am = math.hypot(ax, ay)
            amax = 4.5 * DT
            if am > amax:
                ax, ay = ax / am * amax, ay / am * amax
            v[0] += ax
            v[1] += ay
            nx = clamp(p[0] + v[0] * DT, 0.2, PITCH_LENGTH - 0.2)
            ny = clamp(p[1] + v[1] * DT, 0.2, PITCH_WIDTH - 0.2)
            self.ran[pid] += math.hypot(nx - p[0], ny - p[1])
            p[0], p[1] = nx, ny

    # ------------------------------------------------------------------ on-ball decisions
    def _pressure_events(self) -> None:
        assert self.holder is not None
        h = self.holder
        # A pressing action, not proximity: an opponent who was 8 m+ away when this player got the
        # ball has closed them down. Logged once per spell on the ball.
        if self.spell_start_gap < 8.0 or self.pressed_this_spell:
            return
        for oid in self.on_pitch[self._other(self.side[h])]:
            d = dist(self._p(h), self._p(oid))
            if d < 1.2:
                self.pressed_this_spell = True
                side = self.side[oid]
                self._emit(
                    "pressure",
                    side,
                    oid,
                    self._p(oid),
                    target_player_id=h,
                    intensity=pressure_from_distance(d),
                )
                return

    def _holder_logic(self) -> None:
        h = self.holder
        assert h is not None
        side = self.side[h]
        opp, od = self.nearest_opponent(h)
        minute = self.minute()

        if opp and od < 1.6 and self.t >= self.tackle_cooldown.get(opp, 0) and self.position(h) != "GK":
            forced = self.plan.force_red(self.side[opp], minute)
            if forced or self.rng.random() < 0.05 + 0.05 * self.rating(opp, "defending"):
                self.tackle_cooldown[opp] = self.t + 6.0
                opp_side = self.side[opp]
                where = self._p(h)
                p_win = clamp(
                    0.42 + 0.35 * self.rating(opp, "defending") - 0.25 * self.rating(h, "pace"), 0.15, 0.8
                )
                if not forced and self.rng.random() < p_win:
                    self._emit("tackle", opp_side, opp, where, outcome="won", opponent_id=h)
                    self._give_ball(opp, "tackle", delay=(0.8, 2.0))
                    return
                if forced or self.rng.random() < 0.55:
                    self._emit("tackle", opp_side, opp, where, outcome="lost", opponent_id=h)
                    card = self._book(opp, forced)
                    self._emit("foul", opp_side, opp, where, card=card, meta={"fouled": h})
                    self.dead = DeadBall(self.t + self.rng.uniform(8, 16), side, h, where, "free_kick")
                    self.holder = None
                    return
                self._emit("tackle", opp_side, opp, where, outcome="lost", opponent_id=h)

        if self.carry_target is not None:
            if dist(self._p(h), self.carry_target) < 1.5 or self.t >= self.next_action_t + 3:
                assert self.carry_start is not None
                sx, sy, st = self.carry_start
                length = dist((sx, sy), self._p(h))
                if length > 5:
                    end = self.rel(side, *self._p(h))
                    self._emit(
                        "carry",
                        side,
                        h,
                        (sx, sy),
                        end_x=end[0],
                        end_y=end[1],
                        distance_m=round(length, 1),
                        speed_kmh=round(3.6 * length / max(self.t - st, 0.5), 1),
                    )
                self.carry_target = None
                self.carry_start = None
                self.next_action_t = self.t + self.rng.uniform(0.8, 2.0)
            return

        if self.t < self.next_action_t:
            if od < 2.0 and self.next_action_t - self.t > 0.5:
                # under pressure players release early instead of waiting to be dispossessed
                self.next_action_t = self.t + self.rng.uniform(0.0, 0.5)
            return

        x, y = self._p(h)
        gx = self.goal_x(side)
        dgoal = math.hypot(gx - x, PITCH_WIDTH / 2 - y)
        angle = goal_angle(x, y, gx)
        shot_range = 28 if self.position(h) == "MF" else 26  # midfielders try their luck from distance
        if dgoal < shot_range and self.position(h) != "GK":
            p_shoot = clamp((shot_range - dgoal) / 25 * 0.2 + angle * 0.08, 0, 0.6)
            if self.rng.random() < p_shoot * self.plan.shooting(side, minute):
                self._shoot(h, header=False)
                return

        wide = abs(y - PITCH_WIDTH / 2) > 17
        if wide and abs(gx - x) < 30 and self.position(h) != "GK" and self.rng.random() < 0.35:
            self._pass(h, cross=True)  # wide in the final third: deliver into the box
            return

        p_carry = 0.48 if self.clubs[side].style != "possession" else 0.42
        if self.position(h) == "FW" and abs(self.goal_x(side) - x) < 35:
            p_carry += 0.3  # forwards in the final third run at the defence
        if od > 4 and self.position(h) != "GK" and self.rng.random() < p_carry + 0.25 * (od > 9):
            d = self.direction(side)
            length = self.rng.uniform(6, 18)
            # wide forwards in the final third cut inside toward goal
            inside = 0.45 if self.position(h) == "FW" and abs(self.goal_x(side) - x) < 35 else 0.0
            ty = y + (PITCH_WIDTH / 2 - y) * inside + self.rng.uniform(-6, 6)
            self.carry_target = (clamp(x + d * length, 1, PITCH_LENGTH - 1), clamp(ty, 2, PITCH_WIDTH - 2))
            self.carry_start = (x, y, self.t)
            self.next_action_t = self.t
            return
        self._pass(h)

    def _pass(self, h: str, cross: bool = False) -> None:
        side = self.side[h]
        d = self.direction(side)
        origin = self._p(h)
        _, od = self.nearest_opponent(h)
        pressure = pressure_from_distance(od)
        pressured = od < 3.0
        opponents = [self._p(o) for o in self.on_pitch[self._other(side)]]
        style = self.clubs[side].style

        own_goal_x = PITCH_LENGTH - self.goal_x(side)
        third = abs(origin[0] - own_goal_x) / PITCH_LENGTH
        bias = ROLE_RECEIVE_BIAS["own" if third < 0.34 else "middle" if third < 0.66 else "final"]
        best: tuple[float, str, dict[str, float]] | None = None
        for mate in self.on_pitch[side]:
            if mate == h or (self.position(mate) == "GK" and not pressured):
                continue
            mp = self._p(mate)
            length = dist(origin, mp)
            if length < 4 or length > 60:
                continue
            progress = d * (mp[0] - origin[0])
            openness = min((dist(mp, o) for o in opponents), default=20)
            lane = min((point_segment_distance(o, origin, mp) for o in opponents), default=20)
            progress_weight = 0.01 if pressured else 0.04  # under pressure, safety first
            score = (
                progress_weight * progress
                + 0.22 * min(openness, 8)
                + 0.3 * min(lane, 6)
                - 0.03 * max(0, length - 22)
            )
            # build-up runs through the midfield; forwards are there to finish, not to recycle
            score += bias[self.position(mate)]
            if self.position(h) == "FW" and self.position(mate) == "FW":
                score -= 1.2
            if style == "direct":
                score += 0.012 * progress
            elif style == "possession":
                score -= 0.02 * max(0, length - 15)
            if cross and self.position(mate) != "FW":
                score -= 3
            score += self.rng.gauss(0, 0.9)
            if best is None or score > best[0]:
                best = (score, mate, {"length": length, "lane": lane, "progress": progress})
        if best is None:
            self.next_action_t = self.t + 0.5
            return
        _, mate, info = best
        length, lane = info["length"], info["lane"]
        passing = clamp(self.rating(h, "passing"), 0.2, 1.0)
        logit = (
            2.6
            + 1.6 * passing
            - 0.055 * length
            + 0.35 * min(lane, 5)
            - (1.0 if pressured else 0)
            - (0.5 if length > 30 else 0)
            - (0.9 if cross else 0)
        )
        x_completion = 1 / (1 + math.exp(-logit))
        success = self.rng.random() < x_completion
        speed = clamp((9 + 0.32 * length) * self.rng.uniform(0.9, 1.12), 7, 28)
        err = abs(self.rng.gauss(0, 0.6 + 0.03 * length * (1.1 - passing)))
        ang = self.rng.uniform(0, math.tau)
        mp = self._p(mate)
        end = (
            clamp(mp[0] + math.cos(ang) * err, 0.5, PITCH_LENGTH - 0.5),
            clamp(mp[1] + math.sin(ang) * err, 0.5, PITCH_WIDTH - 0.5),
        )
        interceptor = None
        out_of_play = not success and self.rng.random() < 0.35
        if out_of_play:
            # overhit or miscontrolled: runs out over the touchline
            end = (end[0], 0.0 if end[1] < PITCH_WIDTH / 2 else PITCH_WIDTH)
        elif not success:
            interceptor = min(
                self.on_pitch[self._other(side)],
                key=lambda o: point_segment_distance(self._p(o), origin, end),
            )
            ip = self._p(interceptor)
            frac = clamp(
                ((ip[0] - origin[0]) * (end[0] - origin[0]) + (ip[1] - origin[1]) * (end[1] - origin[1]))
                / max(length**2, 1),
                0.25,
                1.0,
            )
            end = (origin[0] + (end[0] - origin[0]) * frac, origin[1] + (end[1] - origin[1]) * frac)
        self.flight = Flight(
            kind="cross" if cross else "pass",
            passer=h,
            receiver=mate,
            start=origin,
            end=end,
            t0=self.t,
            t1=self.t + max(dist(origin, end) / speed, 0.5),
            speed=speed,
            success=success,
            interceptor=interceptor,
            pressure=pressure,
            data={"x_completion": round(x_completion, 3), "cross": cross},
            out_of_play=out_of_play,
        )
        self.holder = None

    def _advance_flight(self) -> None:
        f = self.flight
        assert f is not None
        u = clamp((self.t - f.t0) / max(f.t1 - f.t0, 0.01), 0, 1)
        self.ball = [f.start[0] + (f.end[0] - f.start[0]) * u, f.start[1] + (f.end[1] - f.start[1]) * u]
        if u < 1:
            return
        if f.kind == "shot":
            self._resolve_shot(f)
            return
        side = self.side[f.passer]
        receiver = f.receiver if f.success else f.interceptor
        if receiver is None or receiver not in self.pos:  # receiver sent off mid-flight
            receiver = min(self.on_pitch[side], key=lambda p: dist(self._p(p), f.end))
        end = self.rel(side, *f.end)
        self._emit(
            "pass",
            side,
            f.passer,
            f.start,
            end_x=end[0],
            end_y=end[1],
            outcome="complete" if f.success else "incomplete",
            receiver_id=f.receiver,
            pressure=f.pressure,
            speed_kmh=round(f.speed * 3.6, 1),
            meta=f.data,
        )
        rp = self.pos[receiver]
        gap = dist((rp[0], rp[1]), f.end)
        if gap > 0:
            step = min(gap, 2.0) / gap
            rp[0] += (f.end[0] - rp[0]) * step
            rp[1] += (f.end[1] - rp[1]) * step
        if not f.success:
            if f.out_of_play:
                taker = min(self.on_pitch[self._other(side)], key=lambda p: dist(self._p(p), f.end))
                spot = (f.end[0], 0.3 if f.end[1] < PITCH_WIDTH / 2 else PITCH_WIDTH - 0.3)
                self.holder = None
                self.dead = DeadBall(
                    self.t + self.rng.uniform(12, 22), self._other(side), taker, spot, "throw_in"
                )
                return
            self._emit("interception", self.side[receiver], receiver, f.end)
            self._give_ball(receiver, "interception")
            return
        if f.kind == "cross" and self.rng.random() < 0.55:
            self.holder = receiver
            self._shoot(receiver, header=True)
            return
        self._give_ball(receiver, "interception")

    def _shoot(self, h: str, header: bool) -> None:
        side = self.side[h]
        x, y = self._p(h)
        gx = self.goal_x(side)
        d = math.hypot(gx - x, PITCH_WIDTH / 2 - y)
        angle = goal_angle(x, y, gx)
        _, od = self.nearest_opponent(h)
        xg = expected_goals(d, angle, od < 2.0, header)
        fin = clamp(self.rating(h, "shooting"), 0.1, 1.0)
        p_goal = clamp(xg * (0.7 + 0.8 * fin) * self.plan.finishing(side, self.minute()), 0.005, 0.95)
        if self.rng.random() < p_goal:
            outcome = "goal"
        else:
            r = self.rng.random()
            outcome = "saved" if r < 0.36 else "blocked" if r < 0.6 else "off_target"
        power = 15 if header else 21 + 9 * fin
        speed = clamp(self.rng.gauss(power, 3.0) - 0.08 * d, 9, 37)
        end_y = PITCH_WIDTH / 2 + self.rng.uniform(-GOAL_HALF_WIDTH * 0.9, GOAL_HALF_WIDTH * 0.9)
        if outcome == "off_target":
            end_y = PITCH_WIDTH / 2 + self.rng.choice([-1, 1]) * self.rng.uniform(4.2, 9)
        end_x = gx
        if outcome == "blocked":
            frac = self.rng.uniform(0.15, 0.45)
            end_x, end_y = x + (gx - x) * frac, y + (end_y - y) * frac
        self.flight = Flight(
            kind="shot",
            passer=h,
            receiver=None,
            start=(x, y),
            end=(end_x, clamp(end_y, 0, PITCH_WIDTH)),
            t0=self.t,
            t1=self.t + max(dist((x, y), (end_x, end_y)) / speed, 0.3),
            speed=speed,
            success=outcome == "goal",
            interceptor=None,
            pressure=pressure_from_distance(od),
            data={"xg": round(xg, 3), "outcome": outcome, "header": header, "distance_m": round(d, 1)},
        )
        self.holder = None

    def _resolve_shot(self, f: Flight) -> None:
        side = self.side[f.passer]
        other = self._other(side)
        outcome = f.data["outcome"]
        self._emit(
            "shot",
            side,
            f.passer,
            f.start,
            outcome=outcome,
            speed_kmh=round(f.speed * 3.6, 1),
            xg=f.data["xg"],
            pressure=f.pressure,
            meta={"header": f.data["header"], "distance_m": f.data["distance_m"]},
        )
        self.flight = None
        keeper = next((p for p in self.on_pitch[other] if self.position(p) == "GK"), self.on_pitch[other][0])
        if outcome == "goal":
            self.score[side] += 1
            taker = self._kickoff_taker(other)
            self.dead = DeadBall(self.t + 60, other, taker, (52.5, 34.0), "kick_off", True)
            return
        if outcome == "saved":
            if self.rng.random() < 0.3:
                self._corner(side)
            else:
                self.pos[keeper] = [f.end[0] - self.direction(side) * 1.0, f.end[1]]
                self._give_ball(keeper, "save", delay=(3, 6))
            return
        if outcome == "blocked":
            if self.rng.random() < 0.35:
                self._corner(side)
            else:
                blocker = min(self.on_pitch[other], key=lambda o: dist(self._p(o), f.end))
                self._give_ball(blocker, "block")
            return
        spot = (abs(self.goal_x(side) - self.direction(side) * 5.5), PITCH_WIDTH / 2)
        self.dead = DeadBall(self.t + self.rng.uniform(10, 18), other, keeper, spot, "goal_kick")

    def _corner(self, side: str) -> None:
        gx = self.goal_x(side)
        cy = self.rng.choice([0.5, PITCH_WIDTH - 0.5])
        outfield = [p for p in self.on_pitch[side] if self.position(p) in ("MF", "FW")] or self.on_pitch[side]
        taker = self.rng.choice(outfield)
        self.dead = DeadBall(self.t + self.rng.uniform(18, 28), side, taker, (abs(gx - 0.5), cy), "corner")

    def _resume(self) -> None:
        db = self.dead
        assert db is not None
        self.dead = None
        if db.taker not in self.on_pitch[db.side]:  # taker was substituted or sent off meanwhile
            db.taker = self._kickoff_taker(db.side)
        if db.kind == "kick_off":
            taker = self._place_for_kickoff(db.side)
            self._emit("kickoff", db.side, taker, self._p(taker), meta={"after_goal": True})
            db.taker = taker
        self.pos[db.taker] = [db.spot[0], db.spot[1]]
        self.ball = [db.spot[0], db.spot[1]]
        self.holder = db.taker
        cause = {
            "goal_kick": "goal_kick",
            "kick_off": "kick_off",
            "free_kick": "foul",
            "corner": "block",
            "throw_in": "throw_in",
        }[db.kind]
        self._give_ball(db.taker, cause, delay=(0.3, 0.6))
        if db.kind == "corner":
            gx = self.goal_x(db.side)
            for pid in self.on_pitch[db.side]:
                if pid != db.taker and self.position(pid) in ("FW", "MF"):
                    self.pos[pid] = [
                        abs(gx - self.rng.uniform(6, 14)),
                        PITCH_WIDTH / 2 + self.rng.uniform(-9, 9),
                    ]
            self._pass(db.taker, cross=True)


# --------------------------------------------------------------------------- public API
def generate_match(
    seed: int,
    storyline: Storyline = "none",
    match_id: str | None = None,
    clubs: dict[str, Club] | None = None,
    home_id: str = "RIV",
    away_id: str = "NOR",
) -> Match:
    """Simulate a full match. Deterministic in ``(seed, storyline)``.

    For storylines other than ``none``, derived sub-seeds are tried in a fixed order until the
    finished match satisfies the storyline.
    """
    clubs = clubs or load_clubs()
    home, away = clubs[home_id], clubs[away_id]
    mid = match_id or f"m{seed}"
    attempts = 1 if storyline == "none" else MAX_STORY_ATTEMPTS
    for i in range(attempts):
        sim_seed = seed if storyline == "none" else seed * 1000 + i
        rng = random.Random(f"{sim_seed}:{storyline}")
        engine = MatchEngine(sim_seed, home, away, plan_for(storyline, rng), mid)
        raw = engine.run()
        if satisfied(storyline, raw, home.club_id):
            return Match(
                match_id=mid,
                seed=seed,
                sim_seed=sim_seed,
                storyline=storyline,
                home=home,
                away=away,
                venue=VENUES[sim_seed % len(VENUES)],
                final_score=(engine.score[HOME], engine.score[AWAY]),
                events=[parse_event(e) for e in raw],
            )
    raise RuntimeError(f"no match satisfied storyline {storyline!r} for seed {seed} in {attempts} attempts")


def write_jsonl(match: Match, path: Path) -> None:
    """One event per line, preceded by nothing: the file is a pure event feed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for ev in match.events:
            f.write(ev.model_dump_json() + "\n")


def _delays(match: Match, speed: float) -> Iterator[tuple[float, MatchEvent]]:
    """(seconds to wait before this event, event) at ``speed``x real time."""
    if speed <= 0:
        raise ValueError("speed must be positive")
    prev: tuple[int, int] | None = None
    for ev in match.events:
        now = (ev.period, ev.clock_seconds)
        wait = 0.0
        if prev is not None:
            # the half-time break is skipped: periods restart the clock at 45:00
            wait = max(0, now[1] - prev[1]) / speed if now[0] == prev[0] else 0.0
        prev = now
        yield wait, ev


def stream_events(
    match: Match, speed: float = 10, sleep: Callable[[float], None] = time.sleep
) -> Iterator[MatchEvent]:
    """Yield events in match order, paced to ``speed``x real time (1, 10, 60, ...)."""
    for wait, ev in _delays(match, speed):
        if wait:
            sleep(wait)
        yield ev


async def astream_events(match: Match, speed: float = 10) -> AsyncIterator[MatchEvent]:
    """Async twin of :func:`stream_events` for the SSE endpoint."""
    for wait, ev in _delays(match, speed):
        if wait:
            await asyncio.sleep(wait)
        yield ev
