"""Explainer agent: one neutral, English, stats-grounded explanation per moment, shared by every fan."""

from __future__ import annotations

from typing import Any

from agent_framework import Agent

from app.agents.fallbacks import render
from app.agents.llm import offline_handler, task_message
from app.moments.models import Moment

INSTRUCTIONS = """You are the Explainer in a live football match-intelligence system. All clubs and players
are fictional. You get one detected moment ("type") and its verified "facts".
Write 1-2 sentences in plain English that say WHY the moment matters (context, consequence, what it reveals),
not just that it happened.
Rules: cite only numbers that appear in facts (you may round); never invent statistics, history, injuries or
quotes; no emoji; at most 45 words. Write every number with digits, never as words: numbers are checked
automatically. Output only the sentences."""


def build(client: Any) -> Agent:
    return Agent(client, INSTRUCTIONS, name="explainer", description="Explains why a moment matters")


def request(moment: Moment) -> str:
    return task_message("explain", type=moment.type, facts=moment.facts)


def fallback(moment: Moment) -> str:
    return render(moment.type, moment.facts, "en", "line")


@offline_handler("explain")
def _offline(task: dict[str, Any]) -> str:
    return render(task.get("type", ""), task.get("facts", {}), "en", "line")
