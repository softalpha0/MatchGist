"""Synthetic tactical-camera video from the simulator's tracking data.

The camera sees what a fixed wide-angle rig would: a green pitch with markings, two kits as coloured discs,
and a white ball drawn on top. Detection never reads the tracking itself, only these frames.
"""

from __future__ import annotations

import random
from collections.abc import Iterator
from dataclasses import dataclass, field

import numpy as np

from app.simulator import engine as sim
from app.simulator.engine import DT, PITCH_LENGTH, PITCH_WIDTH, MatchEngine, generate_match, load_clubs
from app.simulator.storylines import plan_for

PX_PER_M = 6
W, H = int(PITCH_LENGTH * PX_PER_M), int(PITCH_WIDTH * PX_PER_M)
FPS = 10  # tracking is 2 Hz; frames in between are interpolated linearly, as a broadcast would show
GRASS = (34, 110, 60)
LINES = (180, 205, 180)  # deliberately not white, so the ball is the only white object
KITS = {"home": (40, 90, 230), "away": (225, 50, 45)}
BALL = (255, 255, 255)
PLAYER_R_M, BALL_R_M = 0.9, 0.55


@dataclass
class Tick:
    t: float
    period: int
    ball: tuple[float, float]
    players: dict[str, tuple[float, float]]


@dataclass
class TruthPass:
    """Ground truth for one ball flight, captured from the simulator (absolute pitch coordinates)."""

    t0: float
    t1: float
    start: tuple[float, float]
    end: tuple[float, float]
    speed_kmh: float
    success: bool
    kind: str


@dataclass
class Capture:
    ticks: list[Tick] = field(default_factory=list)
    passes: list[TruthPass] = field(default_factory=list)
    home_ids: set[str] = field(default_factory=set)


def capture(seed: int = 42, storyline: str = "none") -> Capture:
    """Re-run the exact simulation behind ``generate_match`` and record every tick and ball flight."""
    match = generate_match(seed, storyline)  # finds the sub-seed that satisfies the storyline
    clubs = load_clubs()
    home, away = clubs[match.home.club_id], clubs[match.away.club_id]
    rng = random.Random(f"{match.sim_seed}:{storyline}")
    eng = MatchEngine(match.sim_seed, home, away, plan_for(storyline, rng), match.match_id)
    cap = Capture(home_ids={p.player_id for p in home.players})
    original, last = eng._move_players, [None]

    def move(reset: bool = False) -> None:
        original(reset)
        f = eng.flight
        # compared by reference: the ids of finished flights get reused
        if f is not None and f is not last[0] and f.kind in ("pass", "cross"):
            last[0] = f
            truth = TruthPass(f.t0, f.t1, f.start, f.end, round(f.speed * 3.6, 1), f.success, f.kind)
            cap.passes.append(truth)
        cap.ticks.append(
            Tick(eng.t, eng.period, (eng.ball[0], eng.ball[1]), {p: (v[0], v[1]) for p, v in eng.pos.items()})
        )

    eng._move_players = move  # type: ignore[method-assign]
    eng.run()
    return cap


def _disc(r_m: float) -> tuple[np.ndarray, np.ndarray]:
    r = r_m * PX_PER_M
    yy, xx = np.mgrid[-int(r) - 1 : int(r) + 2, -int(r) - 1 : int(r) + 2]
    keep = xx**2 + yy**2 <= r * r
    return yy[keep], xx[keep]


PLAYER_DISC, BALL_DISC = _disc(PLAYER_R_M), _disc(BALL_R_M)


def background() -> np.ndarray:
    img = np.empty((H, W, 3), np.uint8)
    img[:] = GRASS
    stripe = (np.arange(W) // (PX_PER_M * 7)) % 2 == 1
    img[:, stripe] = (38, 120, 66)

    def hline(y: float, x0: float, x1: float) -> None:
        img[int(y * PX_PER_M), int(x0 * PX_PER_M) : int(x1 * PX_PER_M)] = LINES

    def vline(x: float, y0: float, y1: float) -> None:
        img[int(y0 * PX_PER_M) : int(y1 * PX_PER_M), min(int(x * PX_PER_M), W - 1)] = LINES

    hline(0, 0, PITCH_LENGTH), hline(PITCH_WIDTH - 0.2, 0, PITCH_LENGTH)
    (
        vline(0, 0, PITCH_WIDTH),
        vline(PITCH_LENGTH - 0.2, 0, PITCH_WIDTH),
        vline(PITCH_LENGTH / 2, 0, PITCH_WIDTH),
    )
    for x0, x1 in ((0, 16.5), (PITCH_LENGTH - 16.5, PITCH_LENGTH)):
        hline(PITCH_WIDTH / 2 - 20.16, x0, x1), hline(PITCH_WIDTH / 2 + 20.16, x0, x1)
    vline(16.5, PITCH_WIDTH / 2 - 20.16, PITCH_WIDTH / 2 + 20.16)
    vline(PITCH_LENGTH - 16.5, PITCH_WIDTH / 2 - 20.16, PITCH_WIDTH / 2 + 20.16)
    a = np.linspace(0, 2 * np.pi, 400)
    cx, cy = PITCH_LENGTH / 2 + 9.15 * np.cos(a), PITCH_WIDTH / 2 + 9.15 * np.sin(a)
    img[(cy * PX_PER_M).astype(int), (cx * PX_PER_M).astype(int)] = LINES
    return img


def _stamp(img: np.ndarray, disc: tuple[np.ndarray, np.ndarray], x_m: float, y_m: float, color) -> None:
    yy = disc[0] + int(round(y_m * PX_PER_M))
    xx = disc[1] + int(round(x_m * PX_PER_M))
    ok = (yy >= 0) & (yy < H) & (xx >= 0) & (xx < W)
    img[yy[ok], xx[ok]] = color


def frames(
    cap: Capture, start_s: float = 0.0, end_s: float | None = None, seed: int = 7
) -> Iterator[tuple[float, np.ndarray]]:
    """Yield ``(time, frame)`` at ``FPS`` with mild sensor noise, interpolating between 2 Hz ticks."""
    bg = background().astype(np.int16)
    noise_rng = np.random.default_rng(seed)
    noise = [noise_rng.integers(-6, 7, size=(H, W, 3), dtype=np.int16) for _ in range(6)]
    sub = int(round(FPS * DT))
    n = 0
    for a, b in zip(cap.ticks, cap.ticks[1:], strict=False):
        if a.t < start_s or b.period != a.period:
            continue
        if end_s is not None and a.t >= end_s:
            break
        for k in range(sub):
            u = k / sub
            img = bg + noise[n % len(noise)]
            n += 1
            np.clip(img, 0, 255, out=img)
            frame = img.astype(np.uint8)
            for pid, (x0, y0) in a.players.items():
                x1, y1 = b.players.get(pid, (x0, y0))
                kit = KITS["home"] if pid in cap.home_ids else KITS["away"]
                _stamp(frame, PLAYER_DISC, x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, kit)
            bx = a.ball[0] + (b.ball[0] - a.ball[0]) * u
            by = a.ball[1] + (b.ball[1] - a.ball[1]) * u
            _stamp(frame, BALL_DISC, bx, by, BALL)
            yield a.t + u * DT, frame


__all__ = ["Capture", "FPS", "PX_PER_M", "TruthPass", "capture", "frames", "sim"]
