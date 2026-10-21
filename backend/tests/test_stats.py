import pytest

from app.moments.detector import ELITE_PASS_DIFFICULTY, MatchAnalyzer
from app.simulator.engine import generate_match
from app.state.match_state import MatchState
from app.stats.metrics import (
    into_final_third,
    is_progressive,
    momentum_points,
    normalise_momentum,
    pass_difficulty,
    pass_distance,
)

# ------------------------------------------------------------------ pure metrics


def test_pass_distance():
    assert pass_distance(0, 0, 3, 4) == 5


def test_progressive_and_final_third():
    assert is_progressive(40, 50) and not is_progressive(40, 49.9)
    assert into_final_third(60, 75) and not into_final_third(72, 90) and not into_final_third(40, 60)


def test_pass_difficulty_spec_formula():
    # 40 m+ (2.5) + full pressure (3) + progressive (2) + into final third (2.5) = 10
    assert pass_difficulty(30, 34, 75, 34, 1.0) == 10.0
    # 20 m sideways, no pressure: 2.5 * 0.5 = 1.25 -> 1.2 (banker's rounding) or 1.3
    assert pass_difficulty(40, 20, 40, 40, 0.0) in (1.2, 1.3)
    # 10 m back pass under half pressure: 0.625 + 1.5
    assert pass_difficulty(50, 34, 40, 34, 0.5) == pytest.approx(2.1, abs=0.05)
    # clipped
    assert 0 <= pass_difficulty(0, 0, 105, 68, 1.0) <= 10


def test_momentum_points_spec():
    assert momentum_points("shot", "off_target") == 3
    assert momentum_points("shot", "blocked") == 3
    assert momentum_points("shot", "saved") == 5
    assert momentum_points("shot", "goal") == 5
    assert momentum_points("pass", "complete", progressive=True) == 1
    assert momentum_points("pass", "complete", progressive=False) == 0
    assert momentum_points("pass", "incomplete", progressive=True) == 0
    assert momentum_points("tackle", "won", x=60) == 2
    assert momentum_points("tackle", "won", x=30) == 0


def test_momentum_normalisation():
    assert normalise_momentum(0, 0) == 0
    assert normalise_momentum(3, 0) < 50  # one early shot is not total dominance
    assert normalise_momentum(40, 0) == 100
    assert normalise_momentum(0, 40) == -100
    assert normalise_momentum(30, 10) == 50


# ------------------------------------------------------------------ engine over a full match


@pytest.fixture(scope="module")
def analysed():
    match = generate_match(42)
    state = MatchState(match)
    analyzer = MatchAnalyzer(state)
    for ev in match.events:
        analyzer.feed(ev)
    return match, state


def test_state_agrees_with_the_feed(analysed):
    match, state = analysed
    assert state.score == match.final_score
    assert state.status == "full_time"
    assert state.events_seen == len(match.events)
    passes = [e for e in match.events if e.type == "pass" and e.team_id == match.home.club_id]
    assert state.teams[match.home.club_id].passes == len(passes)
    assert state.teams[match.home.club_id].passes_completed == sum(e.outcome == "complete" for e in passes)


def test_snapshot_is_sane(analysed):
    _, state = analysed
    snap = state.snapshot(players=True)
    assert snap["home"]["possession"] + snap["away"]["possession"] in (99, 100, 101)
    assert -100 <= snap["momentum"] <= 100
    for side in ("home", "away"):
        assert 0 <= snap[side]["pass_accuracy"] <= 100
        pi = snap[side]["pressure_index"]
        assert pi is None or 0 <= pi <= 1
    assert snap["players"]
    assert {"name", "passes", "xg", "top_shot_speed_kmh"} <= set(next(iter(snap["players"].values())))


def test_series_sampled_every_minute(analysed):
    _, state = analysed
    minutes = [m for m, _ in state.momentum_series]
    assert len(minutes) >= 90
    assert all(-100 <= v <= 100 for _, v in state.momentum_series)


def test_rolling_possession_window(analysed):
    _, state = analysed
    h = state.possession_pct(state.home_id, rolling=True)
    a = state.possession_pct(state.away_id, rolling=True)
    assert h is not None and a is not None and h + a in (99, 100, 101)


# ------------------------------------------------------------------ moments


def test_every_goal_is_a_moment(analysed):
    match, state = analysed
    goals = [m for m in state.moments if m.type == "goal"]
    assert len(goals) == sum(match.final_score)
    for g in goals:
        assert g.base_score == 100
        assert {"player", "xg", "shot_speed_kmh", "team_xg", "opponent_xg", "score"} <= set(g.facts)


def test_period_moments(analysed):
    _, state = analysed
    kinds = [m.type for m in state.moments]
    assert kinds.count("half_time") == 1 and kinds.count("full_time") == 1
    ft = next(m for m in state.moments if m.type == "full_time")
    assert ft.base_score == 90 and ft.facts["top_performer"]


def test_moment_rules(analysed):
    _, state = analysed
    for m in state.moments:
        if m.type == "big_chance":
            assert m.facts["xg"] >= 0.3 and m.facts["outcome"] != "goal"
        if m.type == "elite_pass":
            assert m.facts["difficulty"] >= ELITE_PASS_DIFFICULTY
        if m.type == "momentum_swing":
            assert m.facts["swing"] >= 40
        if m.type == "pressure_spike":
            assert m.facts["pressure_index"] - m.facts["pressure_index_5min_ago"] >= 0.25 - 1e-9
    ids = [m.moment_id for m in state.moments]
    assert len(ids) == len(set(ids))


def test_red_card_moment():
    match = generate_match(42, "red_card")
    state = MatchState(match)
    analyzer = MatchAnalyzer(state)
    for ev in match.events:
        analyzer.feed(ev)
    reds = [m for m in state.moments if m.type == "red_card"]
    assert reds and reds[0].base_score == 85 and reds[0].facts["players_left"] == 10
