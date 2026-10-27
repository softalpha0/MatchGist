from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["ok"] is True


def test_create_match():
    r = client.post("/matches", json={"seed": 42, "speed": 60, "storyline": "none"})
    assert r.status_code == 201
    body = r.json()
    assert body["match_id"].startswith("m") and 1200 <= body["event_count"] <= 1800
    assert body["status"] == "ready"
    assert body["home"] == "Riverside Athletic"


def test_create_match_rejects_unknown_storyline():
    assert client.post("/matches", json={"storyline": "miracle"}).status_code == 422


def test_fans():
    fans = client.get("/fans").json()
    assert [f["fan_id"] for f in fans][:2] == ["fan_london", "fan_jakarta"]


def test_recorder_writes_a_replayable_match_with_evidence() -> None:
    import asyncio

    from app.agents.llm import LLMSettings
    from app.record import evidence_markdown, record

    settings = LLMSettings(None, None, "x", None, "v", None, offline=True, timeout_s=1, retries=0)
    doc = asyncio.run(record("late_drama", 42, settings))
    msgs = doc["messages"]
    times = [m[0] for m in msgs]
    assert times == sorted(times)  # the browser plays them in order
    assert msgs[0][1] == "snapshot" and msgs[0][2]["names"] and msgs[-1][1] == "end"
    moments = [p for _, n, p in msgs if n == "moment"]
    events = {p["event_id"] for _, n, p in msgs if n == "event"}
    assert moments and all(set(m["source_event_ids"]) <= events and m["source_event_ids"] for m in moments)
    assert any(n == "delivery" and p["kind"] == "digest" for _, n, p in msgs)
    md = evidence_markdown(doc)
    assert "Grounding check" in md and "Moments and their source events" in md


def test_add_tracking_inserts_sprints_without_touching_agent_output(tmp_path, monkeypatch) -> None:
    import asyncio
    import json

    from app import record
    from app.agents.llm import LLMSettings

    settings = LLMSettings(None, None, "x", None, "v", None, offline=True, timeout_s=1, retries=0)
    doc = asyncio.run(record.record("late_drama", 42, settings))
    # an older recording, made before the tracking events existed
    doc["messages"] = [m for m in doc["messages"] if m[2].get("type") not in record.TRACKING_TYPES]
    monkeypatch.setattr(record, "REPLAYS", tmp_path)
    (tmp_path / "late_drama.json").write_text(json.dumps(doc))
    before = [m for m in doc["messages"] if m[1] != "event"]
    assert record.add_tracking("late_drama") > 10
    after = json.loads((tmp_path / "late_drama.json").read_text())["messages"]
    assert [m for m in after if m[1] != "event"] == before  # deliveries and agent steps unchanged
    assert [m[0] for m in after] == sorted(m[0] for m in after)
    assert record.add_tracking("late_drama") == 0  # idempotent
