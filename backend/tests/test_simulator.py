from collections import Counter

import pytest

from app.simulator.engine import generate_match, load_clubs, stream_events, write_jsonl
from app.simulator.schema import EVENT_TYPES, PITCH_LENGTH, PITCH_WIDTH, parse_event
from app.simulator.storylines import score_at


def dumps(match):
    return [e.model_dump() for e in match.events]


def test_same_seed_identical_output():
    assert dumps(generate_match(7)) == dumps(generate_match(7))


def test_different_seeds_differ():
    assert dumps(generate_match(7)) != dumps(generate_match(8))


def test_every_event_validates(match42, tmp_path):
    path = tmp_path / "m.jsonl"
    write_jsonl(match42, path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == len(match42.events)
    for line in lines:
        import json

        parse_event(json.loads(line))


@pytest.mark.parametrize("seed", [1, 42, 99])
def test_event_count_and_score_realistic(seed):
    m = generate_match(seed)
    assert 1200 <= len(m.events) <= 1800
    assert sum(m.final_score) <= 9
    goals = Counter(e.team_id for e in m.events if e.type == "shot" and e.outcome == "goal")
    assert (goals[m.home.club_id], goals[m.away.club_id]) == m.final_score


def test_clock_and_seq_always_increase(match42):
    seqs = [e.seq for e in match42.events]
    assert seqs == list(range(1, len(seqs) + 1))
    order = [(e.period, e.clock_seconds) for e in match42.events]
    assert order == sorted(order)
    first_h2 = next(e for e in match42.events if e.period == 2)
    assert first_h2.match_clock == "45:00"


def test_shape_of_a_match(match42):
    types = Counter(e.type for e in match42.events)
    assert types["half_time"] == 1 and types["full_time"] == 1
    assert match42.events[0].type == "kickoff" and match42.events[-1].type == "full_time"
    assert set(types) <= set(EVENT_TYPES)
    for needed in (
        "pass",
        "carry",
        "shot",
        "tackle",
        "interception",
        "foul",
        "possession_change",
        "pressure",
        "substitution",
    ):
        assert types[needed] > 0, needed
    passes = [e for e in match42.events if e.type == "pass"]
    assert 0.75 < sum(e.outcome == "complete" for e in passes) / len(passes) < 0.92


def test_coordinates_valid(match42):
    for e in match42.events:
        for v in (e.x, getattr(e, "end_x", None)):
            assert v is None or 0 <= v <= PITCH_LENGTH
        for v in (e.y, getattr(e, "end_y", None)):
            assert v is None or 0 <= v <= PITCH_WIDTH


def test_ids_reference_real_players(match42):
    known = {p.player_id for c in load_clubs().values() for p in c.players}
    for e in match42.events:
        for pid in (e.player_id, getattr(e, "receiver_id", None), getattr(e, "opponent_id", None)):
            assert pid is None or pid in known


def test_ratings_matter():
    """Shot speed tracks the shooting rating: above-median shooters strike harder."""
    clubs = load_clubs()
    rating = {p.player_id: p.shooting for c in clubs.values() for p in c.players}
    shots = [
        e for s in range(6) for e in generate_match(s).events if e.type == "shot" and not e.meta["header"]
    ]
    median = sorted(rating[e.player_id] for e in shots)[len(shots) // 2]
    strong = [e.speed_kmh for e in shots if rating[e.player_id] > median]
    weak = [e.speed_kmh for e in shots if rating[e.player_id] <= median]
    assert strong and weak
    assert sum(strong) / len(strong) > sum(weak) / len(weak)


def test_comeback():
    m = generate_match(42, "comeback")
    h70, a70 = score_at([e.model_dump() for e in m.events], m.home.club_id, 2, 70)
    assert h70 != a70
    h, a = m.final_score
    assert (h - a >= 0) if h70 < a70 else (a - h >= 0)


def test_late_drama():
    m = generate_match(42, "late_drama")
    late = [
        e
        for e in m.events
        if e.type == "shot" and e.outcome == "goal" and e.period == 2 and e.clock_seconds >= 85 * 60
    ]
    assert late


def test_red_card():
    m = generate_match(42, "red_card")
    assert any(e.type == "foul" and e.card == "red" for e in m.events)


def test_storylines_deterministic():
    assert dumps(generate_match(3, "late_drama")) == dumps(generate_match(3, "late_drama"))


def test_stream_paces_by_speed(match42):
    waits: list[float] = []
    events = list(stream_events(match42, speed=60, sleep=waits.append))
    assert len(events) == len(match42.events)
    # 90+ minutes of play at 60x is about 90 seconds of wall time (half-time break skipped)
    assert 85 < sum(waits) < 110


def test_tracking_indicators_fire_at_thresholds() -> None:
    from collections import defaultdict

    from app.simulator.engine import FIRST_MILESTONE_KM, SPRINT_KMH, generate_match

    m = generate_match(42, "none", "trk")
    sprints = [e for e in m.events if e.type == "sprint"]
    milestones = [e for e in m.events if e.type == "distance_milestone"]
    assert 10 <= len(sprints) <= 150 and milestones
    # thresholds hold, and speeds stay human (players are capped at about 33 km/h in the model)
    assert all(SPRINT_KMH <= e.top_speed_kmh <= 34 and e.distance_m > 0 for e in sprints)
    seen: dict[str, list[int]] = defaultdict(list)
    for e in milestones:
        seen[e.player_id].append(e.total_km)
    assert all(km[0] >= FIRST_MILESTONE_KM and km == sorted(set(km)) for km in seen.values())
    assert max(max(v) for v in seen.values()) <= 13  # a full match is roughly 9-12 km at most
