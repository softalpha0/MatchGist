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
    assert body["home"] == "Riverside Athletic"


def test_create_match_rejects_unknown_storyline():
    assert client.post("/matches", json={"storyline": "miracle"}).status_code == 422


def test_fans():
    fans = client.get("/fans").json()
    assert [f["fan_id"] for f in fans][:2] == ["fan_london", "fan_jakarta"]
