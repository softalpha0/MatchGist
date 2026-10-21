"""Digest agent: the full-time recap, sized to whatever budget the fan has left."""

from __future__ import annotations

from typing import Any

from agent_framework import Agent

from app.agents.fallbacks import first_sentence, render
from app.agents.llm import offline_handler, task_message
from app.channels.limits import Message
from app.channels.sizing import size_kb
from app.channels.sms_encoding import analyze_sms
from app.fans.profiles import FanProfile
from app.moments.models import Moment
from app.state.ledger import Ledger

INSTRUCTIONS = """You are the Digest writer. At full time you write one fan's match recap in their language.
All clubs and players are fictional. You get the full-time facts, the goals, the fan's language and depth,
and a size budget. Tell the story: the result, the decisive moments, and whether the xG numbers say the
result was fair. Use only numbers from the facts; no emoji. Stay inside the size budget you are given.
Output only the recap text."""

DIGEST_MAX_SEGMENTS = 3  # SPEC 6.1 worked example: the digest may use up to 3 SMS segments


def build(client: Any) -> Agent:
    return Agent(client, INSTRUCTIONS, name="digest", description="Full-time recap sized to the fan's budget")


def budget_for(fan: FanProfile, ledger: Ledger) -> dict[str, Any]:
    """How big this fan's digest may be, from what is left."""
    left = ledger.data_left_kb
    match fan.channel:
        case "sms":
            segs = DIGEST_MAX_SEGMENTS if left is None else max(1, min(DIGEST_MAX_SEGMENTS, int(left / 0.2)))
            return {"max_segments": segs}
        case "voice":
            secs = 15.0 if left is None else max(4.0, min(15.0, left * 8 / 16))
            return {"max_seconds": round(secs, 1)}
        case "chat":
            return {"max_chars": 280}
        case _:
            return {}


def request(ft: Moment, fan: FanProfile, budget: dict[str, Any], depth: str) -> str:
    return task_message(
        "digest",
        type="full_time",
        facts=ft.facts,
        language=fan.language,
        channel=fan.channel,
        depth=depth,
        budget=budget,
    )


def template(ft: Moment, language: str, channel: str, depth: str) -> str:
    """Full-time line plus the scorers, in the fan's language."""
    line = render("full_time", ft.facts, language, "line")
    goals = ft.facts.get("goals") or []
    scorers = ", ".join(f"{g['player'].split()[-1]} {g['minute']}'" for g in goals if g.get("player"))
    text = f"{line} {scorers}".strip() if scorers and channel in ("sms", "chat") else line
    return (
        text
        if depth == "analyst" or channel == "chat"
        else first_sentence(text) + (f" {scorers}" if scorers else "")
    )


def fits(text: str, fan: FanProfile, budget: dict[str, Any]) -> bool:
    if fan.channel == "sms":
        return analyze_sms(text).segments <= budget.get("max_segments", 1)
    if fan.channel == "voice":
        return (
            size_kb(Message(channel="voice", text=text, language=fan.language)) * 8 / 16
            <= budget["max_seconds"]
        )
    return True


@offline_handler("digest")
def _offline(task: dict[str, Any]) -> str:
    ft = Moment(
        moment_id="x",
        type="full_time",
        match_clock="90:00",
        period=2,
        minute=90,
        base_score=90,
        facts=task.get("facts", {}),
    )
    return template(ft, task.get("language", "en"), task.get("channel", "sms"), task.get("depth", "casual"))
