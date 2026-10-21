import asyncio
import json

from fastapi.testclient import TestClient

from app.main import app
from app.runtime import MatchRuntime
from app.simulator.engine import generate_match


def read_sse(lines):
    """Parse an SSE line stream into (event, data) pairs."""
    name = None
    for line in lines:
        if line.startswith("event: "):
            name = line[7:]
        elif line.startswith("data: ") and name:
            yield name, json.loads(line[6:])
            name = None


def test_stream_delivers_events_stats_moments_and_end():
    client = TestClient(app)
    created = client.post("/matches", json={"seed": 42, "speed": 10000, "storyline": "none"}).json()
    seen: dict[str, int] = {}
    events = []
    with client.stream("GET", f"/matches/{created['match_id']}/stream") as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        for name, data in read_sse(r.iter_lines()):
            seen[name] = seen.get(name, 0) + 1
            if name == "event":
                events.append(data)
            if name == "end":
                assert data["final_score"] == created["final_score"]
                break
    assert seen["snapshot"] == 1
    assert len(events) == created["event_count"]
    assert seen["moment"] >= 3 and seen["stats"] >= 90
    assert seen["delivery"] >= 10 and seen["agent_event"] >= 50
    assert [e["seq"] for e in events] == sorted(e["seq"] for e in events)

    state = client.get(f"/matches/{created['match_id']}/state").json()
    assert state["snapshot"]["status"] == "full_time"
    assert state["snapshot"]["score"] == created["final_score"]
    assert any(m["type"] == "full_time" for m in state["moments"])
    assert client.get("/matches").json()[-1]["status"] == "finished"


def test_late_joiner_after_full_time_gets_state_and_end():
    client = TestClient(app)
    mid = client.post("/matches", json={"seed": 5, "speed": 10000}).json()["match_id"]
    with client.stream("GET", f"/matches/{mid}/stream") as r:
        for name, _ in read_sse(r.iter_lines()):
            if name == "end":
                break
    with client.stream("GET", f"/matches/{mid}/stream") as r:
        names = [name for name, _ in read_sse(r.iter_lines())]
    assert names[0] == "snapshot" and names[-1] == "end" and "event" not in names
    assert "delivery" in names  # late joiners still see what every fan received


def test_unknown_match_404():
    client = TestClient(app)
    assert client.get("/matches/nope/stream").status_code == 404
    assert client.get("/matches/nope/state").status_code == 404


def test_runtime_shares_one_playback_between_viewers():
    async def scenario():
        rt = MatchRuntime(generate_match(3), speed=10000)
        q1, q2 = rt.subscribe(), rt.subscribe()
        got1, got2 = [], []
        for q, got in ((q1, got1), (q2, got2)):
            while (item := await q.get()) is not None:
                got.append(item)
        return rt, got1, got2

    rt, got1, got2 = asyncio.run(scenario())
    assert rt.done
    count = lambda got, n: sum(1 for name, _ in got if name == n)  # noqa: E731
    assert count(got1, "event") == count(got2, "event") == len(rt.match.events)
    assert got1[-1][0] == got2[-1][0] == "end"


def test_demo_matches_prepared_at_startup():
    with TestClient(app) as client:
        for _ in range(300):
            ids = {m["match_id"] for m in client.get("/matches").json()}
            if {"demo-none", "demo-comeback", "demo-red_card", "demo-late_drama"} <= ids:
                break
            import time

            time.sleep(0.2)
        assert {"demo-none", "demo-comeback", "demo-red_card", "demo-late_drama"} <= ids


def test_replay_ledger_digest_and_add_fan():
    with TestClient(app) as client:
        for _ in range(300):
            if any(m["match_id"] == "demo-late_drama" for m in client.get("/matches").json()):
                break
            import time

            time.sleep(0.2)
        info = client.post("/matches/demo-late_drama/replay", json={"speed": 10000}).json()
        assert info["match_id"].startswith("demo-late_drama-r") and info["status"] == "ready"
        mid = info["match_id"]
        extra = {
            "fan_id": "fan_test",
            "display_name": "Tester",
            "language": "pt-BR",
            "mode": "casual",
            "channel": "sms",
            "data_budget_kb": 50,
            "max_pings": 2,
        }
        assert client.post(f"/matches/{mid}/fans", json=extra).status_code == 201
        assert client.post(f"/matches/{mid}/fans", json=extra).status_code == 409
        with client.stream("GET", f"/matches/{mid}/stream") as r:
            for name, _ in read_sse(r.iter_lines()):
                if name == "end":
                    break
        led = client.get(f"/matches/{mid}/fans/fan_jakarta/ledger").json()
        assert led["pings_used"] <= 4 and led["deliveries"]
        assert client.get(f"/matches/{mid}/fans/fan_jakarta/digest").json()["kind"] == "digest"
        test_led = client.get(f"/matches/{mid}/fans/fan_test/ledger").json()
        assert test_led["pings_used"] <= 2
        cfg = client.get("/config").json()
        assert cfg["llm_mode"] in ("offline", "azure-openai", "foundry")
