import asyncio

import pytest

from touchline.agents import templates
from touchline.agents.director import Director
from touchline.agents.ingest import IngestGate
from touchline.agents.pipeline import MatchPipeline
from touchline.agents.supervisor import Supervisor, verify
from touchline.config import Settings
from touchline.models import Insight, Profile, Side
from touchline.sim.engine import MatchEngine

GOAL_FACTS = {
    "minute": "67'",
    "score": [2, 1],
    "team": "Harbour City FC",
    "opponent": "Redmarsh Town",
    "player": "Ade Varga",
    "xg": 0.06,
    "shot_speed_kmh": 104.2,
    "distance_m": 24.5,
    "team_xg": 1.12,
    "opponent_xg": 1.9,
    "momentum_for_team": -0.4,
    "against_run_of_play": True,
    "low_xg_finish": True,
}


def goal(**kw) -> Insight:
    return Insight(
        id="m1-i1",
        t=4000,
        kind="goal",
        side=Side.HOME,
        player_id="hcf-9",
        importance=1.0,
        facts={**GOAL_FACTS, **kw},
    )


def test_verifier_accepts_grounded_and_rejects_invented():
    assert verify("A 6% chance from 24.5 m at 104 km/h; xG says 1.12 v 1.9.", GOAL_FACTS).ok
    bad = verify("His 7th goal in 3 matches.", GOAL_FACTS)
    assert not bad.ok and "7" in bad.reason
    assert not verify("", GOAL_FACTS).ok


@pytest.mark.parametrize("lang", templates.LANGS)
@pytest.mark.parametrize("mode", ["fan", "analyst"])
def test_templates_are_grounded_in_every_language(lang, mode):
    text = templates.explain("goal", GOAL_FACTS, lang, mode)
    assert text and "{" not in text
    assert verify(text, GOAL_FACTS).ok, text


def test_fan_and_analyst_differ():
    fan = templates.explain("goal", GOAL_FACTS, "en", "fan")
    analyst = templates.explain("goal", GOAL_FACTS, "en", "analyst")
    assert fan != analyst and "xG" in analyst


async def test_supervisor_falls_back_and_opens_breaker():
    sup = Supervisor(model_label="test", timeout_s=0.05, breaker_failures=2, breaker_cooldown_s=60)

    async def boom() -> str:
        raise RuntimeError("down")

    async def slow() -> str:
        await asyncio.sleep(1)
        return "late"

    async def liar() -> str:
        return "That is 99 goals."

    text, trace = await sup.run("analyst", "i1", boom, lambda: "fallback", GOAL_FACTS)
    assert (text, trace.status) == ("fallback", "error")
    text, trace = await sup.run("analyst", "i2", slow, lambda: "fallback", GOAL_FACTS)
    assert trace.status == "timeout" and sup.breaker_open
    text, trace = await sup.run("analyst", "i3", liar, lambda: "fallback", GOAL_FACTS)
    assert trace.status == "breaker_open" and text == "fallback"


async def test_supervisor_rejects_hallucination():
    sup = Supervisor(model_label="test")

    async def liar() -> str:
        return "That is 99 goals."

    text, trace = await sup.run("analyst", "i1", liar, lambda: "safe", GOAL_FACTS)
    assert trace.status == "rejected" and text == "safe"


def test_ingest_repairs_and_quarantines():
    gate = IngestGate({"a-1", "a-2"})
    base = {
        "id": "e1",
        "seq": 5,
        "t": 10.0,
        "type": "pass",
        "side": "home",
        "player_id": "a-1",
        "x": 50,
        "y": 30,
    }
    raw = [
        {**base, "id": "e2", "seq": 6, "x": 160.0},
        base,
        dict(base),
        {**base, "id": "e3", "seq": 7, "player_id": "ghost"},
        {"id": "junk", "type": "teleport"},
    ]
    events, rep = gate.process(raw)
    assert [e.id for e in events] == ["e1", "e2"]
    assert events[1].x == 105.0
    assert (rep.duplicates, rep.quarantined, rep.repaired, rep.resequenced) == (1, 2, 1, 2)


def test_director_personalises_headline_and_filter():
    sprint = Insight(
        id="x",
        t=10,
        kind="sprint",
        side=Side.AWAY,
        player_id="p",
        importance=0.3,
        facts={"player": "P", "speed_kmh": 31.0},
    )
    assert Director(Profile(mode="fan")).cue_for(sprint) is None
    assert Director(Profile(mode="analyst")).cue_for(sprint) is not None
    assert Director(Profile(mode="fan", focus_player_id="p")).cue_for(sprint) is not None
    cue = Director(Profile(mode="fan", language="es", favourite_side=Side.HOME)).cue_for(goal())
    assert cue.headline.startswith("Tu equipo") and "GOL" in cue.headline
    assert cue.slot == "full_panel" and cue.kind == "goal"


async def test_pipeline_end_to_end_with_chaos():
    engine = MatchEngine(5)
    traces = []
    pipe = MatchPipeline(
        engine.meta, Profile(mode="fan", language="fr"), Settings(force_offline=True), on_trace=traces.append
    )
    pipe.chaos.hallucinate_next = 1
    pipe.chaos.fail_next = 1
    updates, cues = [], []
    for frame, events in engine.run():
        out = await pipe.tick([frame], [e.model_dump(mode="json") for e in events])
        cues.extend(out.cues)
        for cue in out.cues:
            if cue.kind in ("goal", "momentum_swing", "half_time", "full_time"):
                updates.append(await pipe.enrich(pipe.insights[cue.insight_id]))
        if frame.minute > 50 and len(updates) > 4:
            break
    statuses = {(t.agent, t.status) for t in traces}
    assert ("analyst", "rejected") in statuses
    assert ("analyst", "error") in statuses
    assert all(u and u.why for u in updates)
    assert any(c.kind == "half_time" for c in cues)
    assert all("7th" not in u.why for u in updates)
