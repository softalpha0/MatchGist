"""Localizer agent: the explanation in the fan's language, tone and depth, with natural football slang."""

from __future__ import annotations

from typing import Any

from agent_framework import Agent

from app.agents.fallbacks import first_sentence, render
from app.agents.llm import offline_handler, task_message
from app.fans.profiles import FanProfile
from app.moments.models import Moment

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi (Devanagari script)",
    "id": "Bahasa Indonesia",
    "pt-BR": "Brazilian Portuguese",
    "ar": "Modern Standard Arabic",
    "pcm": "Nigerian Pidgin",
}

INSTRUCTIONS = """You are the Localizer for a football match-intelligence service. All clubs and players are
fictional. You get a short English explanation of one moment, its verified facts, and one fan's profile.
Rewrite it for that fan:
- language: write entirely in the requested language, the way local football fans actually talk (keep player
  and club names as given; club codes like RIV stay as they are).
- depth "analyst": keep the key numbers. depth "casual": plain words, at most one number.
- if the moment involves the fan's favourite club or player, speak to them as a supporter, but stay fair.
Rules: use only numbers from the facts; add no new facts; no emoji; at most 40 words. Output only the text.
Write every number with digits ("2-1", "89'"), never as words: numbers are checked automatically."""


def depth(fan: FanProfile) -> str:
    return "analyst" if fan.mode in ("analyst", "single_metric") else "casual"


def build(client: Any) -> Agent:
    return Agent(client, INSTRUCTIONS, name="localizer", description="Language, tone and depth for one fan")


def request(moment: Moment, fan: FanProfile, explanation: str) -> str:
    return task_message(
        "localize",
        type=moment.type,
        facts=moment.facts,
        explanation=explanation,
        language=fan.language,
        language_name=LANGUAGE_NAMES.get(fan.language, fan.language),
        depth=depth(fan),
        favorite_club=fan.favorite_club,
        favorite_player=fan.favorite_player,
    )


def fallback(moment: Moment, fan: FanProfile) -> str:
    line = render(moment.type, moment.facts, fan.language, "line")
    return line if depth(fan) == "analyst" else first_sentence(line)


@offline_handler("localize")
def _offline(task: dict[str, Any]) -> str:
    line = render(task.get("type", ""), task.get("facts", {}), task.get("language", "en"), "line")
    return line if task.get("depth") == "analyst" else first_sentence(line)
