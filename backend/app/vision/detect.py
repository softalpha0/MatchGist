"""Pass and ball-speed detection from video frames alone (no access to the simulator).

Per frame: the ball is the white blob; the team in possession is the kit colour touching the ball. A pass
is the ball leaving one team's control, travelling, and being controlled again. Distance and ball speed come
from the ball's pixel track.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np

from app.vision.render import PX_PER_M

CONTROL_M = 1.0  # ball within this distance of a kit pixel = under that team's control
MIN_PASS_M = 4.0
CONTROL_KMH = 28.0  # a ball moving faster than a dribble is in flight, even when it passes close to a player
PASS_PEAK_KMH = 27.0  # a flight must reach kicking speed somewhere; slower "flights" are loose dribbles
MAX_BALL_KMH = 150.0  # faster than any kick: the ball was re-spotted for a restart, not passed
WIN = int(CONTROL_M * PX_PER_M) + 2


@dataclass
class Detected:
    t_release: float
    t_receive: float
    start: tuple[float, float]
    end: tuple[float, float]
    team: str
    completed: bool
    distance_m: float
    speed_kmh: float


def find_ball(frame: np.ndarray) -> tuple[float, float] | None:
    m = (frame[:, :, 0] > 235) & (frame[:, :, 1] > 235) & (frame[:, :, 2] > 235)
    ys, xs = np.nonzero(m)
    if len(xs) < 3:
        return None
    return float(xs.mean()) / PX_PER_M, float(ys.mean()) / PX_PER_M


def controlling_team(frame: np.ndarray, ball: tuple[float, float]) -> str | None:
    """Which kit is touching the ball, by the nearest coloured pixel in a small window around it."""
    bx, by = int(ball[0] * PX_PER_M), int(ball[1] * PX_PER_M)
    y0, x0 = max(by - WIN, 0), max(bx - WIN, 0)
    win = frame[y0 : by + WIN + 1, x0 : bx + WIN + 1].astype(np.int16)
    r, g, b = win[:, :, 0], win[:, :, 1], win[:, :, 2]
    best: tuple[float, str] | None = None
    for team, mask in (("home", (b > 170) & (r < 110)), ("away", (r > 170) & (b < 110) & (g < 110))):
        ys, xs = np.nonzero(mask)
        if len(xs):
            d = float(np.min(np.hypot(xs + x0 - bx, ys + y0 - by))) / PX_PER_M
            if d <= CONTROL_M and (best is None or d < best[0]):
                best = (d, team)
    return best[1] if best else None


def steps_peak(held, flight, ball, t) -> float:  # type: ignore[no-untyped-def]
    """Fastest frame-to-frame ball speed over a flight, km/h."""
    pts = [(held[1], held[2]), *flight, (t, ball)]
    return max(
        (
            math.dist(a[1], b[1]) / (b[0] - a[0]) * 3.6
            for a, b in zip(pts, pts[1:], strict=False)
            if b[0] > a[0]
        ),
        default=0.0,
    )


def detect(frames: Iterable[tuple[float, np.ndarray]]) -> list[Detected]:
    out: list[Detected] = []
    held: tuple[str, float, tuple[float, float]] | None = None  # team, time, ball position at release
    flight: list[tuple[float, tuple[float, float]]] = []
    prev: tuple[float, tuple[float, float]] | None = None
    jumped = False
    for t, frame in frames:
        ball = find_ball(frame)
        if ball is None:
            continue
        kmh = math.dist(prev[1], ball) / max(t - prev[0], 1e-6) * 3.6 if prev else 0.0
        if kmh > MAX_BALL_KMH:
            jumped = True  # a cut or a re-spot (free kick, kick-off): whatever was in flight isn't a pass
        prev = (t, ball)
        team = controlling_team(frame, ball) if kmh < CONTROL_KMH else None
        if team is None:
            if held is not None:
                flight.append((t, ball))
            continue
        if held is not None and flight and not jumped:
            start, end = held[2], ball
            d = math.dist(start, end)
            if d >= MIN_PASS_M and steps_peak(held, flight, ball, t) >= PASS_PEAK_KMH:
                path = [held[2]] + [p for _, p in flight] + [ball]
                times = [held[1]] + [s for s, _ in flight] + [t]
                steps = [
                    math.dist(a, b) / (tb - ta)
                    for a, b, ta, tb in zip(path, path[1:], times, times[1:], strict=False)
                    if tb > ta
                ]
                # median step speed: robust to the partial frames around each touch
                speed = sorted(steps)[len(steps) // 2] * 3.6 if steps else 0.0
                out.append(
                    Detected(held[1], t, start, end, held[0], team == held[0], round(d, 1), round(speed, 1))
                )
        held, flight, jumped = (team, t, ball), [], False
    return out
