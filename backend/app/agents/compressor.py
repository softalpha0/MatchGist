"""Compressor agent: fits the localized text to the channel's hard limit, working in the target language.

It runs after the Localizer because translation changes length, and one Hindi or Arabic letter (or a
Portuguese "ç") switches an SMS from 160 to 70 characters. When the Verifier rejects an attempt, its exact
reason is fed back here for the next try.
"""

from __future__ import annotations

import json
from typing import Any

from agent_framework import Agent

from app.agents.fallbacks import LATIN, compose, strip_accents
from app.agents.llm import offline_handler, parse_json_reply, task_message
from app.channels.limits import (
    CHAT_MAX_CHARS,
    PUSH_MAX_BODY,
    PUSH_MAX_TITLE,
    VOICE_MAX_SECONDS,
    WATCH_MAX_CHARS,
    Message,
)
from app.channels.sms_encoding import analyze_sms, gsm_safe

INSTRUCTIONS = """You are the Compressor. You rewrite a football update so it fits one delivery channel's HARD
limit, in the SAME language you are given. Keep names, the score and the single most important number.
Channel limits:
- sms: at most `max_segments` SMS segments. GSM-7 text: 160 chars for 1 segment (153 per segment when split).
  ANY character outside GSM-7 (Hindi, Arabic, emoji, curly quotes, Portuguese ç/ã/õ/ê) makes the whole SMS
  UCS-2: 70 chars for 1 segment (67 when split). For Latin-script languages prefer plain ASCII letters.
- chat: at most 280 characters.
- voice: a spoken sentence of at most 15 seconds (about 30 words); no abbreviations, no club codes.
- watch: "text" at most 40 characters with NO digits, plus "value": the one number to show (e.g. "2-1").
- push: "title" at most 50 characters and "text" (body) at most 100 characters.
Use only numbers from the facts. If "feedback" is present, your previous attempt was rejected for that reason:
fix exactly that.
Reply with JSON only: {"text": "...", "title": "...", "value": "..."} (omit keys the channel doesn't use)."""

LIMITS = {
    "sms": "max_segments segments",
    "chat": f"{CHAT_MAX_CHARS} chars",
    "voice": f"{VOICE_MAX_SECONDS:.0f} seconds spoken",
    "watch": f"text {WATCH_MAX_CHARS} chars, no digits, plus one value",
    "push": f"title {PUSH_MAX_TITLE} chars, body {PUSH_MAX_BODY} chars",
}


def build(client: Any) -> Agent:
    return Agent(client, INSTRUCTIONS, name="compressor", description="Fits text to a channel's hard limit")


def request(
    *,
    text: str,
    mtype: str,
    facts: dict[str, Any],
    language: str,
    channel: str,
    depth: str,
    max_segments: int,
    attempt: int,
    feedback: str | None,
) -> str:
    current = analyze_sms(text) if channel == "sms" else None
    return task_message(
        "compress",
        text=text,
        type=mtype,
        facts=facts,
        language=language,
        channel=channel,
        limit=LIMITS.get(channel, ""),
        max_segments=max_segments,
        depth=depth,
        attempt=attempt,
        feedback=feedback,
        current=None
        if current is None
        else {
            "encoding": current.encoding,
            "units": current.units,
            "segments": current.segments,
        },
    )


def to_message(reply: str, channel: str, language: str) -> Message | None:
    data = parse_json_reply(reply)
    if data is None:
        return (
            None
            if channel in ("watch", "push")
            else Message(channel=channel, text=reply.strip(), language=language)
        )
    text = str(data.get("text") or "").strip()
    return Message(
        channel=channel,
        text=text,
        title=(str(data["title"]).strip() if data.get("title") else None),
        value=(str(data["value"]).strip() if data.get("value") not in (None, "") else None),
        language=language,
    )


@offline_handler("compress")
def _offline(task: dict[str, Any]) -> str:
    """Deterministic strategy: attempt 1 passes the text through (tidied); later attempts use templates.

    That mirrors what a model does on a first pass, and it means the Verifier-and-retry loop is exercised
    (and visible) even without a model.
    """
    channel = task.get("channel", "sms")
    language = task.get("language", "en")
    text = task.get("text", "")
    if task.get("attempt", 1) == 1 and channel not in ("watch", "push"):
        if channel == "sms" and language in LATIN:
            text = gsm_safe(text)
        return json.dumps({"text": text}, ensure_ascii=False)
    msg = compose(
        task.get("type", ""),
        task.get("facts", {}),
        language,
        channel,
        task.get("depth", "casual"),
        task.get("max_segments", 1),
    )
    if channel == "sms" and language in LATIN and analyze_sms(msg.text).encoding == "UCS-2":
        msg = Message(channel="sms", text=strip_accents(msg.text), language=language)
    return json.dumps({"text": msg.text, "title": msg.title, "value": msg.value}, ensure_ascii=False)
