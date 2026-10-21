"""The language agents: Microsoft Agent Framework ``Agent``s with narrow, distinct roles."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from agent_framework import Agent, AgentResponse, Message, agent_middleware

ANALYST_INSTRUCTIONS = """You are the Analyst agent in a live football broadcast graphics pipeline.
You receive a JSON task describing one detected moment ("kind") and the verified "facts" about it.
Write 1-2 sentences in English that explain WHY the moment matters: its context, consequence or what it
reveals about the game. Do not just restate that it happened.
Rules: cite only numbers that appear in facts (you may round them); never invent statistics, history, injuries,
transfer news or quotes; no emoji or hashtags; at most 45 words. Output only the sentences."""

PERSONALIZER_INSTRUCTIONS = """You are the Personalizer agent. You adapt an analyst's explanation of a football moment for
one viewer, described by "profile":
- mode "fan": warm, vivid, plain words, at most one number. mode "analyst": precise, keep the key numbers.
- language: write entirely in that language (en, es, fr or pt).
- favourite_club: if the moment involves that club, speak to the viewer as its supporter, without being unfair
  to the opponent.
- focus_player: if the moment involves that player, put them at the centre.
Rules: cite only numbers that appear in facts; never add facts that are not given; at most 40 words.
Output only the final text."""

NARRATOR_INSTRUCTIONS = """You are the Narrator agent. At half-time and full-time you write the studio recap for one viewer
("profile": mode, language, favourite_club). Using only the facts and the key moments provided, write at most
3 sentences: the story of the half or match, the decisive moments, and what the numbers (xG, shots, possession)
say about whether the score is fair. Cite only numbers present in the input. Write in the profile language.
Output only the recap."""


@dataclass
class ChaosControls:
    """Fault injection used in the demo to show recovery. Applies to any backend."""

    fail_next: int = 0
    hallucinate_next: int = 0
    slow_next: int = 0
    slow_seconds: float = 12.0


def make_chaos_middleware(controls: ChaosControls):
    @agent_middleware
    async def chaos(context, call_next):  # type: ignore[no-untyped-def]
        if controls.fail_next > 0:
            controls.fail_next -= 1
            raise RuntimeError("injected model outage")
        if controls.slow_next > 0:
            controls.slow_next -= 1
            await asyncio.sleep(controls.slow_seconds)
        await call_next()
        if controls.hallucinate_next > 0 and isinstance(context.result, AgentResponse):
            controls.hallucinate_next -= 1
            invented = (context.result.text or "") + " It is his 7th goal in 3 matches."
            context.result = AgentResponse(messages=Message("assistant", [invented]))

    return chaos


@dataclass
class AgentTeam:
    analyst: Agent
    personalizer: Agent
    narrator: Agent
    model_label: str


def build_team(client: Any, model_label: str, controls: ChaosControls) -> AgentTeam:
    mw = [make_chaos_middleware(controls)]
    return AgentTeam(
        analyst=Agent(
            client,
            ANALYST_INSTRUCTIONS,
            name="analyst",
            description="Explains why a moment matters",
            middleware=mw,
        ),
        personalizer=Agent(
            client,
            PERSONALIZER_INSTRUCTIONS,
            name="personalizer",
            description="Adapts intelligence to one viewer",
            middleware=mw,
        ),
        narrator=Agent(
            client,
            NARRATOR_INSTRUCTIONS,
            name="narrator",
            description="Writes half-time and full-time recaps",
            middleware=mw,
        ),
        model_label=model_label,
    )


def task_message(task: str, **payload: Any) -> str:
    """JSON task envelope shared by every language agent (and parsed by the offline backend)."""
    return json.dumps({"task": task, **payload}, ensure_ascii=False, default=str)
