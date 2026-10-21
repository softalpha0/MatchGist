from collections import Counter

import pytest

from touchline.analytics.moments import MomentDetector, clock_label
from touchline.analytics.state import MatchState
from touchline.sim.engine import MatchEngine


@pytest.fixture(scope="module")
def analysed():
    engine = MatchEngine(11)
    state = MatchState(engine.meta)
    det = MomentDetector(state)
    insights = []
    for frame, events in engine.run():
        started = state.apply_frame(frame)
        for e in events:
            state.apply_event(e)
            insights.extend(det.on_event(e))
        insights.extend(det.on_sprints(started, frame.t))
        insights.extend(det.on_clock(frame.t))
    return engine, state, insights


def test_physical_numbers_are_human(analysed):
    _, state, _ = analysed
    outfield = [p for pid, p in state.players.items() if not pid.endswith("-1")]
    assert all(p.top_speed * 3.6 < 38 for p in outfield)
    avg_km = sum(p.distance for p in outfield) / len(outfield) / 1000
    assert 7 < avg_km < 14


def test_state_matches_feed(analysed):
    engine, state, _ = analysed
    assert state.score == [engine.score[s] for s in ("home", "away")]
    snap = state.snapshot()
    assert snap["home"]["possession"] + snap["away"]["possession"] in (99, 100, 101)
    assert 0 <= snap["control"]["chaos"] <= 100
    assert -1 <= snap["momentum"] <= 1


def test_every_goal_becomes_an_insight(analysed):
    engine, _, insights = analysed
    kinds = Counter(i.kind for i in insights)
    assert kinds["goal"] == sum(engine.score.values())
    assert kinds["full_time"] == 1 and kinds["half_time"] == 1


def test_insights_explain_with_facts(analysed):
    _, _, insights = analysed
    for ins in insights:
        assert ins.facts, ins.kind
        assert 0 <= ins.importance <= 1
    goal = next((i for i in insights if i.kind == "goal"), None)
    if goal:
        for key in ("xg", "team_xg", "opponent_xg", "against_run_of_play"):
            assert key in goal.facts


def test_clock_label():
    assert clock_label(1, 22.4) == "23'"
    assert clock_label(1, 46.2) == "45+2'"
    assert clock_label(2, 91.0) == "90+2'"
