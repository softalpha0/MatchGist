import json

from fastapi.testclient import TestClient

from touchline.server.app import app


def test_health_and_schema():
    client = TestClient(app)
    assert client.get("/api/health").json()["ok"]
    schema = client.get("/api/schema/cue").json()
    assert {"t_in", "t_out", "slot", "headline", "why"} <= set(schema["properties"])
    assert client.get("/").status_code == 200


def test_websocket_streams_frames_and_cues():
    client = TestClient(app)
    profile = json.dumps({"mode": "analyst", "language": "en"})
    with client.websocket_connect(f"/ws/match?seed=7&speed=64&profile={profile}") as ws:
        hello = ws.receive_json()
        assert hello["type"] == "hello" and hello["seed"] == 7
        ws.send_text(json.dumps({"type": "profile", "profile": {"mode": "fan", "language": "pt"}}))
        seen = set()
        for _ in range(400):
            msg = ws.receive_json()
            seen.add(msg["type"])
            if {"frame", "cue", "stats"} <= seen:
                break
        assert {"frame", "cue", "stats"} <= seen
