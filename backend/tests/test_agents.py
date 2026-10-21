import asyncio
from typing import Any

import pytest
from agent_framework import BaseChatClient, ChatResponse, Message

from app.agents import fallbacks
from app.agents.budget_guard import decide, threshold
from app.agents.llm import LLMSettings, OfflineChatClient
from app.agents.orchestrator import Orchestrator
from app.agents.ranker import rank
from app.agents.verifier import normalise_digits, verify
from app.channels.limits import Message as Msg
from app.channels.sms_encoding import analyze_sms
from app.fans.profiles import FanProfile, load_fans
from app.moments.detector import MatchAnalyzer
from app.moments.models import Moment
from app.simulator.engine import generate_match
from app.state.ledger import Ledger
from app.state.match_state import MatchState

GOAL = Moment(
    moment_id="m-1",
    type="goal",
    match_clock="66:40",
    period=2,
    minute=67,
    team_id="RIV",
    player_id="RIV-09",
    involved_player_ids=["RIV-09", "RIV-10"],
    base_score=100,
    facts={
        "minute": 67,
        "score": "2-1",
        "home": "Riverside Athletic",
        "away": "Northgate Rovers",
        "home_code": "RIV",
        "away_code": "NOR",
        "team_code": "RIV",
        "team": "Riverside Athletic",
        "opponent": "Northgate Rovers",
        "player": "Dmytro Lysenko-Vale",
        "xg": 0.31,
        "shot_speed_kmh": 104.2,
        "team_xg": 1.4,
        "opponent_xg": 0.9,
        "assist": "Matteo Calvisano",
    },
)
SETTINGS = LLMSettings(None, None, "x", None, "v", None, offline=True, timeout_s=1, retries=2, backoff_s=0)


def fan(**kw: Any) -> FanProfile:
    base = dict(
        fan_id="f",
        display_name="F",
        language="en",
        mode="casual",
        channel="sms",
        data_budget_kb=1024,
        max_pings=4,
    )
    return FanProfile(**{**base, **kw})


# ------------------------------------------------------------------ fallbacks


@pytest.mark.parametrize("lang", fallbacks.LANGUAGES)
@pytest.mark.parametrize(
    "mtype",
    [
        "goal",
        "red_card",
        "big_chance",
        "momentum_swing",
        "half_time",
        "full_time",
        "pressure_spike",
        "elite_pass",
        "yellow_card",
    ],
)
def test_every_template_exists_in_every_language(lang, mtype):
    for form in ("short", "line", "watch"):
        assert fallbacks.T[lang][mtype][form]


@pytest.mark.parametrize("lang", fallbacks.LANGUAGES)
@pytest.mark.parametrize("channel", ["sms", "chat", "voice", "watch", "push"])
def test_fallback_always_fits_and_is_grounded(lang, channel):
    msg = fallbacks.compose("goal", GOAL.facts, lang, channel, "analyst", max_segments=1)
    v = verify(msg, GOAL.facts, max_segments=1)
    assert v.ok, (lang, channel, v.reasons, msg)


def test_strip_accents_keeps_portuguese_in_gsm7():
    text = "Esquível marca, que emoção! Ação total"
    assert analyze_sms(text).encoding == "UCS-2"
    assert analyze_sms(fallbacks.strip_accents(text)).encoding == "GSM-7"


# ------------------------------------------------------------------ verifier


def test_verifier_rejects_invented_numbers_in_any_script():
    assert not verify(Msg(channel="sms", text="His 7th goal this season"), GOAL.facts).ok
    assert verify(Msg(channel="sms", text="GOAL RIV 2-1 NOR (67') xG 0.31"), GOAL.facts).ok
    # Devanagari digits are checked like ASCII ones
    assert normalise_digits("स्कोर २-१") == "स्कोर 2-1"
    assert verify(Msg(channel="sms", text="स्कोर २-१"), GOAL.facts).ok
    assert not verify(Msg(channel="sms", text="स्कोर ७-०"), GOAL.facts).ok


def test_verifier_enforces_segment_allowance():
    hindi_72 = "ग" * 72
    assert not verify(Msg(channel="sms", text=hindi_72), {}, max_segments=1).ok
    assert verify(Msg(channel="sms", text=hindi_72), {}, max_segments=2).ok


# ------------------------------------------------------------------ ranker and guard


def test_ranker_spec_adjustments():
    assert rank(fan(favorite_club="RIV"), GOAL).score == 130
    assert rank(fan(favorite_club="RIV", favorite_player="RIV-10", mode="player_focus"), GOAL).score == 170
    r = rank(fan(favorite_club="NOR", only_if_involved=True), GOAL)
    assert r.skip and r.score == 60
    assert rank(fan(focus_metric="xg", mode="single_metric"), GOAL).score == 120


def test_threshold_rises_as_pings_run_out():
    led = Ledger.for_fan(fan())
    assert threshold(led) == 50
    led.pings_used = 2
    assert threshold(led) == 70
    assert threshold(Ledger.for_fan(fan(max_pings=None))) == 50


def test_guard_rules():
    f = fan(favorite_club="RIV")
    led = Ledger.for_fan(f)
    assert decide(f, led, GOAL, rank(f, GOAL)).action == "send"
    swing = GOAL.model_copy(
        update={"type": "momentum_swing", "base_score": 55, "player_id": None, "involved_player_ids": []}
    )
    d = decide(f, led, swing, rank(f, swing))
    assert d.action == "hold" and "bundle" in d.reason
    led.pings_used = 2  # two left: kept for a goal and the digest
    d = decide(f, led, swing, rank(f, swing))
    assert d.action == "skip" and "kept for" in d.reason
    led.pings_used = 4
    assert decide(f, led, GOAL, rank(f, GOAL)).action == "skip"
    assert (
        decide(
            fan(channel="broadcast", data_budget_kb=None, max_pings=None),
            led,
            swing,
            rank(fan(channel="broadcast"), swing),
        ).action
        == "send"
    )


# ------------------------------------------------------------------ full chain


class FailingClient(BaseChatClient):
    """A model that is always down."""

    def _inner_get_response(self, *, messages, stream, options, **kwargs):
        async def boom() -> ChatResponse:
            raise RuntimeError("model outage")

        return boom()


class LiarClient(BaseChatClient):
    """A model that invents a number every time."""

    def _inner_get_response(self, *, messages, stream, options, **kwargs):
        async def lie() -> ChatResponse:
            return ChatResponse(messages=Message("assistant", ['{"text": "It is his 777th goal in 123 games!"}']))

        return lie()


def run_match(seed: int, storyline: str, client: Any = None) -> tuple[Orchestrator, list[tuple[str, dict]]]:
    async def go():
        m = generate_match(seed, storyline)
        state = MatchState(m)
        analyzer = MatchAnalyzer(state)
        out: list[tuple[str, dict]] = []
        clients = (
            (client, client, "test") if client else (OfflineChatClient(), OfflineChatClient(), "offline")
        )
        orch = Orchestrator(state, load_fans(), lambda n, p: out.append((n, p)), SETTINGS, clients=clients)
        for ev in m.events:
            for mo in analyzer.feed(ev):
                await orch.on_moment(mo)
            if ev.type != "full_time":
                await orch.tick(state.minute)
        return orch, out

    return asyncio.run(go())


@pytest.fixture(scope="module")
def offline_run():
    return run_match(42, "late_drama")


def test_every_persona_stays_within_limits(offline_run):
    orch, out = offline_run
    for s in orch.sessions.values():
        led = s.ledger
        if led.max_pings is not None:
            assert led.pings_used <= led.max_pings, s.fan.fan_id
        if led.data_budget_kb is not None:
            assert led.data_used_kb <= led.data_budget_kb
        for d in led.deliveries:
            msg = Msg(
                channel=d.channel,
                text=d.text,
                title=d.title,
                value=d.value,
                language=d.language,
                audio_seconds=d.audio_seconds,
            )
            allowance = 3 if d.kind == "digest" else 2
            assert verify(msg, {}, None, allowance).reasons in (
                [],
                *[[r] for r in verify(msg, {}).reasons if r.startswith("numbers")],
            ), d


def test_every_fan_gets_a_digest_and_events_are_logged(offline_run):
    orch, out = offline_run
    for s in orch.sessions.values():
        kinds = [d.kind for d in s.ledger.deliveries]
        assert kinds, s.fan.fan_id
        if s.fan.channel != "broadcast":
            assert kinds[-1] == "digest", s.fan.fan_id
    agents = {p["agent"] for n, p in out if n == "agent_event"}
    assert {"explainer", "ranker", "budget_guard", "localizer", "compressor", "verifier", "digest"} <= agents
    reasons = [p["detail"] for n, p in out if n == "agent_event" and p["agent"] == "budget_guard"]
    assert all(reasons)


def test_jakarta_only_hears_about_riverside(offline_run):
    orch, _ = offline_run
    jak = orch.sessions["fan_jakarta"]
    for d in jak.ledger.deliveries:
        if d.kind != "digest":
            assert "Riverside" in d.text or "RIV" in d.text


def test_hindi_sms_reject_then_rewrite_is_visible(offline_run):
    _, out = offline_run
    rejects = [
        p
        for n, p in out
        if n == "agent_event"
        and p["agent"] == "verifier"
        and p["action"] == "reject"
        and p["fan_id"] == "fan_delhi"
    ]
    assert rejects and "UCS-2" in rejects[0]["detail"]


def test_model_outage_falls_back_and_feed_continues():
    orch, out = run_match(7, "none", FailingClient())
    deliveries = [p for n, p in out if n == "delivery"]
    assert deliveries and all(d["fallback_used"] for d in deliveries if d["channel"] != "broadcast")
    assert any(p["action"] == "fallback" for n, p in out if n == "agent_event")


def test_hallucinating_model_is_caught_by_verifier():
    orch, out = run_match(7, "none", LiarClient())
    texts = [p["text"] for n, p in out if n == "delivery"]
    assert texts and not any("777" in t for t in texts)
    assert any(
        p["agent"] == "verifier" and p["action"] in ("reject", "fallback")
        for n, p in out
        if n == "agent_event"
    )
