"""Seeded, football-realistic match simulator.

The engine is a generator: every 0.5 s of match time it yields one tracking
``Frame`` plus whatever ``MatchEvent``s happened in that tick, exactly like a
live event-and-tracking feed. Nothing is pre-computed, so the downstream
agents genuinely see the match unfold.

The model is intentionally simple but grounded:
  * players move toward tactical targets with speed and acceleration limits,
    so distance and sprint numbers come out in realistic ranges;
  * pass success follows an expected-completion model (distance, passing
    lane, pressure, passer quality) and that probability doubles as the pass
    difficulty rating;
  * shots use a distance/angle expected-goals model.
"""

from __future__ import annotations

import math
import random
from collections.abc import Iterator
from dataclasses import dataclass, field

from touchline.models import (
    PITCH_LENGTH,
    PITCH_WIDTH,
    Club,
    EventType,
    Frame,
    MatchEvent,
    MatchMeta,
    Player,
    Position,
    Side,
)
from touchline.sim.clubs import CLUBS, FORMATION, VENUES, build_squad

DT = 0.5
HALF_SECONDS = 45 * 60
GOAL_HALF_WIDTH = 3.66


def clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v


def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def point_segment_distance(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    seg = dx * dx + dy * dy
    if seg == 0:
        return dist(p, a)
    u = clamp(((p[0] - ax) * dx + (p[1] - ay) * dy) / seg, 0.0, 1.0)
    return dist(p, (ax + u * dx, ay + u * dy))


def expected_goals(distance: float, angle: float, pressured: bool, header: bool) -> float:
    """Logistic xG from distance (m) and visible goal-mouth angle (rad)."""
    logit = -1.1 - 0.12 * distance + 1.6 * angle
    if pressured:
        logit -= 0.6
    if header:
        logit -= 0.7
    return 1.0 / (1.0 + math.exp(-logit))


def goal_angle(x: float, y: float, goal_x: float) -> float:
    a = math.atan2(PITCH_WIDTH / 2 + GOAL_HALF_WIDTH - y, abs(goal_x - x))
    b = math.atan2(PITCH_WIDTH / 2 - GOAL_HALF_WIDTH - y, abs(goal_x - x))
    return abs(a - b)


@dataclass
class Flight:
    kind: str  # pass | shot | cross
    passer: str
    receiver: str | None
    start: tuple[float, float]
    end: tuple[float, float]
    t0: float
    t1: float
    speed: float
    success: bool
    interceptor: str | None
    data: dict = field(default_factory=dict)


@dataclass
class DeadBall:
    resume_t: float
    side: Side
    taker: str
    spot: tuple[float, float]
    kind: str  # kick_off | free_kick | goal_kick | corner
    reset_shape: bool = False


class MatchEngine:
    def __init__(self, seed: int, home_id: str | None = None, away_id: str | None = None):
        self.rng = random.Random(seed)
        self.seed = seed
        home, away = self._pick_clubs(home_id, away_id)
        self.clubs: dict[Side, Club] = {Side.HOME: home, Side.AWAY: away}
        squads = {
            Side.HOME: build_squad(home, Side.HOME, self.rng),
            Side.AWAY: build_squad(away, Side.AWAY, self.rng),
        }
        self.players: dict[str, Player] = {p.id: p for s in squads.values() for p in s}
        self.slot: dict[str, int] = {p.id: i for s in squads.values() for i, p in enumerate(s)}
        self.team: dict[Side, list[str]] = {side: [p.id for p in squads[side]] for side in Side}
        self.meta = MatchMeta(
            match_id=f"m{seed}",
            seed=seed,
            home=home,
            away=away,
            venue=self.rng.choice(VENUES),
            players=list(self.players.values()),
        )
        self.stoppage = (self.rng.randint(1, 3) * 60, self.rng.randint(2, 5) * 60)
        self.pos: dict[str, list[float]] = {}
        self.vel: dict[str, list[float]] = {pid: [0.0, 0.0] for pid in self.players}
        self.phase_offset = {pid: self.rng.uniform(0, math.tau) for pid in self.players}
        self.t = 0.0
        self.period = 1
        self.period_start = 0.0
        self.seq = 0
        self.score = {Side.HOME: 0, Side.AWAY: 0}
        self.holder: str | None = None
        self.flight: Flight | None = None
        self.dead: DeadBall | None = None
        self.ball = [PITCH_LENGTH / 2, PITCH_WIDTH / 2]
        self.ball_smooth = [PITCH_LENGTH / 2, PITCH_WIDTH / 2]
        self.next_action_t = 0.0
        self.carry_target: tuple[float, float] | None = None
        self.carry_start: tuple[float, float, float] | None = None
        self.tackle_cooldown: dict[str, float] = {}
        self.last_pressure: dict[tuple[str, str], float] = {}
        self.possession_side = Side.HOME
        self.finished = False

    # ------------------------------------------------------------------ setup
    def _pick_clubs(self, home_id: str | None, away_id: str | None) -> tuple[Club, Club]:
        by_id = {c.id: c for c in CLUBS}
        if home_id and away_id:
            return by_id[home_id], by_id[away_id]
        pair = self.rng.sample(CLUBS, 2)
        return pair[0], pair[1]

    def direction(self, side: Side) -> int:
        """+1 if ``side`` attacks toward x=105 in the current period."""
        base = 1 if side is Side.HOME else -1
        return base if self.period == 1 else -base

    def goal_x(self, side: Side) -> float:
        """x of the goal that ``side`` is attacking."""
        return PITCH_LENGTH if self.direction(side) == 1 else 0.0

    def minute(self) -> float:
        base = 0.0 if self.period == 1 else 45.0
        return base + (self.t - self.period_start) / 60.0

    def _place_for_kickoff(self, kicking: Side) -> None:
        for side, ids in self.team.items():
            d = self.direction(side)
            for pid in ids:
                _, fx, fy = FORMATION[self.slot[pid]]
                rel = clamp(fx * 0.75, 0.02, 0.47)
                x = PITCH_LENGTH / 2 - d * (0.5 - rel) * PITCH_LENGTH
                self.pos[pid] = [x, fy * PITCH_WIDTH]
                self.vel[pid] = [0.0, 0.0]
        taker = self.team[kicking][9]
        self.pos[taker] = [PITCH_LENGTH / 2, PITCH_WIDTH / 2]
        self.ball = [PITCH_LENGTH / 2, PITCH_WIDTH / 2]

    # ------------------------------------------------------------------ events
    def _event(self, etype: EventType, **kw) -> MatchEvent:
        self.seq += 1
        data = kw.pop("data", {})
        data.setdefault("minute", round(self.minute(), 2))
        data.setdefault("period", self.period)
        return MatchEvent(
            id=f"{self.meta.match_id}-{self.seq}",
            seq=self.seq,
            t=round(self.t, 2),
            type=etype,
            data=data,
            **kw,
        )

    def side_of(self, pid: str) -> Side:
        return self.players[pid].side

    def _p(self, pid: str) -> tuple[float, float]:
        return (self.pos[pid][0], self.pos[pid][1])

    def nearest_opponent(self, pid: str) -> tuple[str, float]:
        me = self._p(pid)
        best, bd = "", 1e9
        for oid in self.team[self.side_of(pid).other]:
            d = dist(me, self._p(oid))
            if d < bd:
                best, bd = oid, d
        return best, bd

    def _give_ball(
        self, pid: str, events: list[MatchEvent], reason: str, delay: tuple[float, float] = (0.8, 2.4)
    ) -> None:
        side = self.side_of(pid)
        if side is not self.possession_side:
            self.possession_side = side
            events.append(
                self._event(
                    EventType.POSSESSION_CHANGE,
                    side=side,
                    player_id=pid,
                    x=round(self.pos[pid][0], 1),
                    y=round(self.pos[pid][1], 1),
                    data={"reason": reason},
                )
            )
        self.holder = pid
        self.flight = None
        self.carry_target = None
        self.carry_start = None
        self.next_action_t = self.t + self.rng.uniform(*delay)

    # ------------------------------------------------------------------ main loop
    def run(self) -> Iterator[tuple[Frame, list[MatchEvent]]]:
        events: list[MatchEvent] = []
        self._place_for_kickoff(Side.HOME)
        events.append(
            self._event(
                EventType.KICK_OFF,
                side=Side.HOME,
                data={
                    "home": self.clubs[Side.HOME].name,
                    "away": self.clubs[Side.AWAY].name,
                    "venue": self.meta.venue,
                },
            )
        )
        self._give_ball(self.team[Side.HOME][9], events, "kick_off", delay=(0.5, 0.5))
        while not self.finished:
            yield self._frame(), events
            events = []
            self.t += DT
            self._step(events)
        yield self._frame(), events

    def _frame(self) -> Frame:
        return Frame(
            t=round(self.t, 2),
            period=self.period,
            minute=round(self.minute(), 3),
            ball=(round(self.ball[0], 2), round(self.ball[1], 2)),
            players={pid: (round(p[0], 2), round(p[1], 2)) for pid, p in self.pos.items()},
        )

    def _step(self, events: list[MatchEvent]) -> None:
        elapsed = self.t - self.period_start
        limit = HALF_SECONDS + self.stoppage[self.period - 1]
        if elapsed >= limit and self.flight is None:
            self._end_period(events)
            return

        if self.dead is not None:
            self._move_players(reset=self.dead.reset_shape)
            if self.t >= self.dead.resume_t:
                self._resume(events)
            return

        if self.flight is not None:
            self._advance_flight(events)
        elif self.holder is not None:
            self._holder_logic(events)

        self._move_players()
        if self.holder is not None:
            d = self.direction(self.side_of(self.holder))
            self.ball = [self.pos[self.holder][0] + 0.6 * d, self.pos[self.holder][1]]
            self._pressure_events(events)

    def _end_period(self, events: list[MatchEvent]) -> None:
        if self.period == 1:
            events.append(
                self._event(
                    EventType.HALF_TIME, data={"score": [self.score[Side.HOME], self.score[Side.AWAY]]}
                )
            )
            self.period = 2
            self.period_start = self.t
            self._place_for_kickoff(Side.AWAY)
            events.append(self._event(EventType.KICK_OFF, side=Side.AWAY, data={"second_half": True}))
            self.possession_side = Side.HOME  # forces a possession_change event
            self._give_ball(self.team[Side.AWAY][9], events, "kick_off", delay=(0.5, 0.5))
        else:
            events.append(
                self._event(
                    EventType.FULL_TIME, data={"score": [self.score[Side.HOME], self.score[Side.AWAY]]}
                )
            )
            self.finished = True

    # ------------------------------------------------------------------ movement
    def _targets(self, reset: bool) -> dict[str, tuple[float, float, bool]]:
        """Return target (x, y, urgent) per player.

        Team shape follows a smoothed ball position so that a long pass does
        not make all twenty outfielders sprint at once.
        """
        bx, by = self.ball_smooth
        out: dict[str, tuple[float, float, bool]] = {}
        for side, ids in self.team.items():
            d = self.direction(side)
            own_goal = 0.0 if d == 1 else PITCH_LENGTH
            ball_rel = (bx - own_goal) * d / PITCH_LENGTH
            attacking = side is self.possession_side
            for pid in ids:
                pos, fx, fy = FORMATION[self.slot[pid]]
                if pos is Position.GK:
                    rel = clamp(0.02 + 0.1 * ball_rel, 0.01, 0.12)
                    ty = PITCH_WIDTH / 2 + (by - PITCH_WIDTH / 2) * 0.2
                else:
                    push = 0.10 if attacking else -0.04
                    if attacking and pos is Position.FW:
                        push += 0.06
                    rel = fx + (ball_rel - 0.5) * 0.6 + push
                    if reset:
                        rel = min(rel * 0.75, 0.47)
                    rel = clamp(rel, 0.03, 0.95)
                    width = 0.95 if attacking else 0.7
                    ty = (
                        PITCH_WIDTH / 2
                        + (fy * PITCH_WIDTH - PITCH_WIDTH / 2) * width
                        + (by - PITCH_WIDTH / 2) * 0.25
                    )
                ph = self.phase_offset[pid] + self.t * 0.15
                tx = own_goal + d * rel * PITCH_LENGTH + 2.5 * math.sin(ph)
                ty += 2.0 * math.cos(ph * 1.3)
                out[pid] = (clamp(tx, 0.5, PITCH_LENGTH - 0.5), clamp(ty, 0.5, PITCH_WIDTH - 0.5), False)

        if reset or self.dead is not None:
            return out

        # defending side: the two closest outfielders engage the ball
        defending = self.possession_side.other
        bx, by = self.ball
        ball = (bx, by)
        chasers = sorted(
            (pid for pid in self.team[defending] if self.players[pid].position is not Position.GK),
            key=lambda pid: dist(self._p(pid), ball),
        )[:2]
        if chasers:
            out[chasers[0]] = (bx, by, dist(self._p(chasers[0]), ball) < 18)
        if len(chasers) > 1:
            gx = 0.0 if self.direction(defending) == 1 else PITCH_LENGTH
            out[chasers[1]] = ((bx + gx) / 2 * 0.3 + bx * 0.7, by, False)

        if self.flight is not None and self.flight.receiver:
            r = self.flight.interceptor or self.flight.receiver
            out[r] = (self.flight.end[0], self.flight.end[1], True)
        if self.holder is not None and self.carry_target is not None:
            out[self.holder] = (self.carry_target[0], self.carry_target[1], True)
        elif self.holder is not None:
            hx, hy = self._p(self.holder)
            out[self.holder] = (hx, hy, False)
        return out

    def _move_players(self, reset: bool = False) -> None:
        k = DT / 2.5
        self.ball_smooth[0] += (self.ball[0] - self.ball_smooth[0]) * k
        self.ball_smooth[1] += (self.ball[1] - self.ball_smooth[1]) * k
        targets = self._targets(reset)
        for pid, (tx, ty, urgent) in targets.items():
            p = self.pos[pid]
            v = self.vel[pid]
            dx, dy = tx - p[0], ty - p[1]
            d = math.hypot(dx, dy)
            pace = clamp(self.players[pid].pace, 0.2, 1.0)
            vmax = (6.6 + 2.6 * pace) if urgent else min(1.0 + 0.16 * d, 5.0)
            if pid == self.holder:
                vmax = min(vmax, 5.5 + 2.0 * pace)
            desired = (dx / d * min(vmax, d / DT), dy / d * min(vmax, d / DT)) if d > 0.05 else (0.0, 0.0)
            amax = 4.5 * DT
            ax, ay = desired[0] - v[0], desired[1] - v[1]
            am = math.hypot(ax, ay)
            if am > amax:
                ax, ay = ax / am * amax, ay / am * amax
            v[0] += ax
            v[1] += ay
            p[0] = clamp(p[0] + v[0] * DT, 0.2, PITCH_LENGTH - 0.2)
            p[1] = clamp(p[1] + v[1] * DT, 0.2, PITCH_WIDTH - 0.2)

    # ------------------------------------------------------------------ ball logic
    def _pressure_events(self, events: list[MatchEvent]) -> None:
        assert self.holder is not None
        h = self.holder
        for oid in self.team[self.side_of(h).other]:
            d = dist(self._p(h), self._p(oid))
            if d < 2.5 and self.t - self.last_pressure.get((oid, h), -99) > 10:
                self.last_pressure[(oid, h)] = self.t
                events.append(
                    self._event(
                        EventType.PRESSURE,
                        side=self.side_of(oid),
                        player_id=oid,
                        target_id=h,
                        x=round(self.pos[h][0], 1),
                        y=round(self.pos[h][1], 1),
                        data={"distance": round(d, 2)},
                    )
                )

    def _holder_logic(self, events: list[MatchEvent]) -> None:
        h = self.holder
        assert h is not None
        side = self.side_of(h)
        opp, od = self.nearest_opponent(h)

        # tackle attempt by the closest opponent
        if (
            od < 1.6
            and self.t >= self.tackle_cooldown.get(opp, 0)
            and self.players[h].position is not Position.GK
        ):
            tk = self.players[opp]
            if self.rng.random() < 0.035 + 0.04 * tk.tackling:
                self.tackle_cooldown[opp] = self.t + 6.0
                p_win = clamp(0.42 + 0.35 * tk.tackling - 0.25 * self.players[h].pace, 0.15, 0.8)
                xy = {"x": round(self.pos[h][0], 1), "y": round(self.pos[h][1], 1)}
                if self.rng.random() < p_win:
                    events.append(
                        self._event(
                            EventType.TACKLE, side=tk.side, player_id=opp, target_id=h, outcome="won", **xy
                        )
                    )
                    self._give_ball(opp, events, "tackle", delay=(0.6, 1.6))
                    return
                if self.rng.random() < 0.4:
                    events.append(self._event(EventType.FOUL, side=tk.side, player_id=opp, target_id=h, **xy))
                    if self.rng.random() < 0.16:
                        events.append(
                            self._event(EventType.CARD, side=tk.side, player_id=opp, outcome="yellow", **xy)
                        )
                    self.dead = DeadBall(self.t + self.rng.uniform(8, 16), side, h, self._p(h), "free_kick")
                    self.holder = None
                    return
                events.append(
                    self._event(
                        EventType.TACKLE, side=tk.side, player_id=opp, target_id=h, outcome="lost", **xy
                    )
                )

        if self.carry_target is not None:
            if dist(self._p(h), self.carry_target) < 1.5 or self.t >= self.next_action_t + 3:
                assert self.carry_start is not None
                sx, sy, st = self.carry_start
                length = dist((sx, sy), self._p(h))
                if length > 3:
                    events.append(
                        self._event(
                            EventType.CARRY,
                            side=side,
                            player_id=h,
                            x=round(sx, 1),
                            y=round(sy, 1),
                            end_x=round(self.pos[h][0], 1),
                            end_y=round(self.pos[h][1], 1),
                            data={
                                "distance": round(length, 1),
                                "speed": round(length / max(self.t - st, 0.5), 2),
                            },
                        )
                    )
                self.carry_target = None
                self.carry_start = None
                self.next_action_t = self.t + self.rng.uniform(0.2, 0.8)
            return

        if self.t < self.next_action_t:
            return

        x, y = self._p(h)
        gx = self.goal_x(side)
        dgoal = math.hypot(gx - x, PITCH_WIDTH / 2 - y)
        angle = goal_angle(x, y, gx)
        if dgoal < 25 and self.players[h].position is not Position.GK:
            p_shoot = clamp((25 - dgoal) / 25 * 0.13 + angle * 0.05, 0, 0.5)
            if self.clubs[side].style == "direct":
                p_shoot += 0.02
            if self.rng.random() < p_shoot:
                self._shoot(h, events, header=False)
                return

        style = self.clubs[side].style
        p_carry = {"possession": 0.3, "direct": 0.34, "pressing": 0.32, "balanced": 0.34}[style]
        if (
            od > 5
            and self.players[h].position is not Position.GK
            and self.rng.random() < p_carry + 0.25 * (od > 9)
        ):
            d = self.direction(side)
            length = self.rng.uniform(5, 16)
            self.carry_target = (
                clamp(x + d * length, 1, PITCH_LENGTH - 1),
                clamp(y + self.rng.uniform(-6, 6), 2, PITCH_WIDTH - 2),
            )
            self.carry_start = (x, y, self.t)
            self.next_action_t = self.t
            return

        self._pass(h, events)

    def _pass(self, h: str, events: list[MatchEvent], cross: bool = False) -> None:
        side = self.side_of(h)
        d = self.direction(side)
        passer = self.players[h]
        origin = self._p(h)
        _, pressure_d = self.nearest_opponent(h)
        pressured = pressure_d < 3.0
        opponents = [self._p(o) for o in self.team[side.other]]
        style = self.clubs[side].style

        best: tuple[float, str, dict] | None = None
        for mate in self.team[side]:
            if mate == h:
                continue
            if self.players[mate].position is Position.GK and not pressured:
                continue
            mp = self._p(mate)
            length = dist(origin, mp)
            if length < 4 or length > 60:
                continue
            progress = d * (mp[0] - origin[0])
            openness = min(dist(mp, o) for o in opponents)
            lane = min(point_segment_distance(o, origin, mp) for o in opponents)
            score = (
                0.05 * progress + 0.22 * min(openness, 8) + 0.3 * min(lane, 6) - 0.03 * max(0, length - 22)
            )
            if style == "direct":
                score += 0.03 * progress
            elif style == "possession":
                score -= 0.02 * max(0, length - 15)
            if cross and self.players[mate].position is not Position.FW:
                score -= 3
            score += self.rng.gauss(0, 0.9)
            if best is None or score > best[0]:
                best = (
                    score,
                    mate,
                    {"length": length, "lane": lane, "progress": progress, "openness": openness},
                )
        if best is None:
            self.next_action_t = self.t + 0.5
            return
        _, mate, info = best
        length, lane = info["length"], info["lane"]
        long_ball = length > 30
        logit = (
            2.6
            + 1.6 * clamp(passer.passing, 0.2, 1.0)
            - 0.055 * length
            + 0.35 * min(lane, 5)
            - (1.0 if pressured else 0)
            - (0.5 if long_ball else 0)
            - (0.9 if cross else 0)
        )
        x_completion = 1 / (1 + math.exp(-logit))
        success = self.rng.random() < x_completion
        speed = clamp((9 + 0.32 * length) * self.rng.uniform(0.9, 1.12), 7, 28)
        err = abs(self.rng.gauss(0, 0.6 + 0.03 * length * (1.1 - clamp(passer.passing, 0.2, 1.0))))
        end = self._p(mate)
        ang = self.rng.uniform(0, math.tau)
        end = (
            clamp(end[0] + math.cos(ang) * err, 0.5, PITCH_LENGTH - 0.5),
            clamp(end[1] + math.sin(ang) * err, 0.5, PITCH_WIDTH - 0.5),
        )
        interceptor = None
        if not success:
            interceptor = min(
                self.team[side.other],
                key=lambda o: point_segment_distance(self._p(o), origin, end),
            )
            ip = self._p(interceptor)
            # ball is cut out roughly where the interceptor meets the lane
            frac = clamp(
                ((ip[0] - origin[0]) * (end[0] - origin[0]) + (ip[1] - origin[1]) * (end[1] - origin[1]))
                / max(length**2, 1),
                0.25,
                1.0,
            )
            end = (origin[0] + (end[0] - origin[0]) * frac, origin[1] + (end[1] - origin[1]) * frac)
        flight_len = dist(origin, end)
        t1 = self.t + max(flight_len / speed, 0.5)
        self.flight = Flight(
            kind="cross" if cross else "pass",
            passer=h,
            receiver=mate,
            start=origin,
            end=end,
            t0=self.t,
            t1=t1,
            speed=speed,
            success=success,
            interceptor=interceptor,
            data={
                "length": round(length, 1),
                "x_completion": round(x_completion, 3),
                "difficulty": round(1 - x_completion, 3),
                "accuracy": round(clamp(1 - err / 6, 0, 1), 3),
                "progressive": info["progress"] > 10,
                "lane_clearance": round(lane, 2),
                "pressured": pressured,
                "speed": round(speed, 2),
                "cross": cross,
                "long_ball": long_ball,
            },
        )
        self.holder = None

    def _advance_flight(self, events: list[MatchEvent]) -> None:
        f = self.flight
        assert f is not None
        u = clamp((self.t - f.t0) / max(f.t1 - f.t0, 0.01), 0, 1)
        self.ball = [f.start[0] + (f.end[0] - f.start[0]) * u, f.start[1] + (f.end[1] - f.start[1]) * u]
        if u < 1:
            return
        if f.kind == "shot":
            self._resolve_shot(f, events)
            return
        side = self.side_of(f.passer)
        receiver = f.receiver if f.success else f.interceptor
        assert receiver is not None
        # pull the receiver onto the ball (bounded, so tracking stays physical)
        rp = self.pos[receiver]
        gap = dist((rp[0], rp[1]), f.end)
        if gap > 0:
            step = min(gap, 2.0) / gap
            rp[0] += (f.end[0] - rp[0]) * step
            rp[1] += (f.end[1] - rp[1]) * step
        events.append(
            self._event(
                EventType.PASS,
                side=side,
                player_id=f.passer,
                target_id=f.receiver,
                x=round(f.start[0], 1),
                y=round(f.start[1], 1),
                end_x=round(f.end[0], 1),
                end_y=round(f.end[1], 1),
                outcome="complete" if f.success else "intercepted",
                data={**f.data, "t_start": round(f.t0, 2)},
            )
        )
        if not f.success:
            events.append(
                self._event(
                    EventType.INTERCEPTION,
                    side=side.other,
                    player_id=receiver,
                    x=round(f.end[0], 1),
                    y=round(f.end[1], 1),
                )
            )
            self._give_ball(receiver, events, "interception")
            return
        # a completed cross into the box becomes a header chance
        if f.kind == "cross" and self.rng.random() < 0.55:
            self.holder = receiver
            self._shoot(receiver, events, header=True)
            return
        self._give_ball(receiver, events, "pass")

    def _shoot(self, h: str, events: list[MatchEvent], header: bool) -> None:
        side = self.side_of(h)
        x, y = self._p(h)
        gx = self.goal_x(side)
        d = math.hypot(gx - x, PITCH_WIDTH / 2 - y)
        angle = goal_angle(x, y, gx)
        _, od = self.nearest_opponent(h)
        xg = expected_goals(d, angle, od < 2.0, header)
        fin = clamp(self.players[h].finishing, 0.1, 1.0)
        p_goal = clamp(xg * (0.65 + 0.7 * fin), 0.005, 0.95)
        roll = self.rng.random()
        if roll < p_goal:
            outcome = "goal"
        else:
            rest = self.rng.random()
            outcome = "saved" if rest < 0.36 else "blocked" if rest < 0.6 else "off_target"
        speed = clamp(self.rng.gauss(26 if not header else 15, 3.5) - 0.08 * d, 9, 37)
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
            end=(end_x, end_y),
            t0=self.t,
            t1=self.t + max(dist((x, y), (end_x, end_y)) / speed, 0.3),
            speed=speed,
            success=outcome == "goal",
            interceptor=None,
            data={
                "xg": round(xg, 3),
                "distance": round(d, 1),
                "angle": round(math.degrees(angle), 1),
                "speed": round(speed, 2),
                "speed_kmh": round(speed * 3.6, 1),
                "header": header,
                "pressured": od < 2.0,
                "outcome": outcome,
            },
        )
        self.holder = None

    def _resolve_shot(self, f: Flight, events: list[MatchEvent]) -> None:
        side = self.side_of(f.passer)
        outcome = f.data["outcome"]
        shot = self._event(
            EventType.SHOT,
            side=side,
            player_id=f.passer,
            x=round(f.start[0], 1),
            y=round(f.start[1], 1),
            end_x=round(f.end[0], 1),
            end_y=round(f.end[1], 1),
            outcome=outcome,
            data={**f.data, "t_start": round(f.t0, 2)},
        )
        events.append(shot)
        keeper = self.team[side.other][0]
        if outcome == "goal":
            self.score[side] += 1
            events.append(
                self._event(
                    EventType.GOAL,
                    side=side,
                    player_id=f.passer,
                    x=shot.x,
                    y=shot.y,
                    data={
                        "score": [self.score[Side.HOME], self.score[Side.AWAY]],
                        "xg": f.data["xg"],
                        "shot_id": shot.id,
                        "speed_kmh": f.data["speed_kmh"],
                        "distance": f.data["distance"],
                    },
                )
            )
            self.flight = None
            self.dead = DeadBall(
                self.t + 40, side.other, self.team[side.other][9], (52.5, 34.0), "kick_off", True
            )
            return
        if outcome == "saved":
            events.append(
                self._event(EventType.SAVE, side=side.other, player_id=keeper, x=shot.end_x, y=shot.end_y)
            )
            if self.rng.random() < 0.3:
                self._corner(side, events)
            else:
                self.pos[keeper] = [f.end[0] - self.direction(side) * 1.0, f.end[1]]
                self._give_ball(keeper, events, "save", delay=(3, 6))
            return
        if outcome == "blocked":
            self.flight = None
            if self.rng.random() < 0.35:
                self._corner(side, events)
            else:
                blocker = min(self.team[side.other], key=lambda o: dist(self._p(o), f.end))
                self.pos[blocker] = [f.end[0], f.end[1]]
                self._give_ball(blocker, events, "block")
            return
        # off target: goal kick
        self.flight = None
        gk_spot = (abs(self.goal_x(side) - self.direction(side) * 5.5), PITCH_WIDTH / 2)
        self.dead = DeadBall(self.t + self.rng.uniform(10, 18), side.other, keeper, gk_spot, "goal_kick")

    def _corner(self, side: Side, events: list[MatchEvent]) -> None:
        self.flight = None
        gx = self.goal_x(side)
        cy = self.rng.choice([0.5, PITCH_WIDTH - 0.5])
        taker = self.team[side][self.rng.choice([7, 8, 10])]
        events.append(self._event(EventType.CORNER, side=side, player_id=taker, x=gx, y=cy))
        self.dead = DeadBall(self.t + self.rng.uniform(18, 28), side, taker, (abs(gx - 0.5), cy), "corner")

    def _resume(self, events: list[MatchEvent]) -> None:
        db = self.dead
        assert db is not None
        self.dead = None
        if db.kind == "kick_off":
            self._place_for_kickoff(db.side)
            events.append(self._event(EventType.KICK_OFF, side=db.side, data={"after_goal": True}))
        self.pos[db.taker] = [db.spot[0], db.spot[1]]
        self.ball = [db.spot[0], db.spot[1]]
        self._give_ball(db.taker, events, db.kind, delay=(0.3, 0.6))
        if db.kind == "corner":
            # attackers crowd the box
            gx = self.goal_x(db.side)
            for pid in self.team[db.side][5:]:
                if pid != db.taker:
                    self.pos[pid] = [
                        abs(gx - self.rng.uniform(6, 14)),
                        PITCH_WIDTH / 2 + self.rng.uniform(-9, 9),
                    ]
            self._pass(db.taker, events, cross=True)
