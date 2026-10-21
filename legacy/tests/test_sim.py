from collections import Counter

import pytest

from touchline.models import PITCH_LENGTH, PITCH_WIDTH, EventType
from touchline.sim.engine import MatchEngine, expected_goals


def run(seed: int):
    engine = MatchEngine(seed)
    frames, events = [], []
    for frame, evs in engine.run():
        frames.append(frame)
        events.extend(evs)
    return engine, frames, events


@pytest.fixture(scope="module")
def match():
    return run(7)


def test_same_seed_same_match():
    _, _, a = run(3)
    _, _, b = run(3)
    assert [e.model_dump() for e in a] == [e.model_dump() for e in b]


def test_full_match_shape(match):
    engine, frames, events = match
    kinds = Counter(e.type for e in events)
    assert kinds[EventType.HALF_TIME] == 1
    assert kinds[EventType.FULL_TIME] == 1
    assert frames[-1].minute >= 90
    # football-realistic volumes for a 90 minute game
    assert 800 < kinds[EventType.PASS] < 2000
    assert 8 < kinds[EventType.SHOT] < 60
    assert kinds[EventType.GOAL] == sum(engine.score.values())


def test_pass_completion_is_realistic(match):
    _, _, events = match
    passes = [e for e in events if e.type is EventType.PASS]
    rate = sum(e.outcome == "complete" for e in passes) / len(passes)
    assert 0.7 < rate < 0.9


def test_coordinates_and_order(match):
    _, frames, events = match
    assert all(0 <= e.x <= PITCH_LENGTH and 0 <= e.y <= PITCH_WIDTH for e in events if e.x is not None)
    seqs = [e.seq for e in events]
    assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs)
    ts = [f.t for f in frames]
    assert ts == sorted(ts)


def test_pass_metrics_present(match):
    _, _, events = match
    p = next(e for e in events if e.type is EventType.PASS)
    for key in ("length", "x_completion", "difficulty", "accuracy", "speed"):
        assert key in p.data
    assert abs(p.data["difficulty"] + p.data["x_completion"] - 1) < 1e-6


def test_xg_model_monotonic():
    assert expected_goals(6, 1.0, False, False) > expected_goals(20, 0.3, False, False)
    assert expected_goals(10, 0.6, True, False) < expected_goals(10, 0.6, False, False)
