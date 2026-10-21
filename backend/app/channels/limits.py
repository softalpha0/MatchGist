"""Hard per-channel limits (SPEC section 6), enforced in code by the Verifier.

A delivery is described by a :class:`Message`. :func:`check` returns every violated limit with a
reason a person can read, plus the measurements behind it (segments, characters, seconds).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from app.channels.sms_encoding import analyze_sms
from app.fans.profiles import Channel

SMS_MAX_SEGMENTS = 2
SMS_PREFERRED_SEGMENTS = 1
CHAT_MAX_CHARS = 280
VOICE_MAX_SECONDS = 15.0
WATCH_MAX_CHARS = 40
WATCH_MAX_VALUE_CHARS = 8
PUSH_MAX_TITLE = 50
PUSH_MAX_BODY = 100

# Speaking rate used to estimate a voice note's length before text-to-speech runs (words per second).
# Real durations come from Azure AI Speech in M4; this estimate lets the Compressor aim correctly.
SPEECH_WORDS_PER_SECOND = {"en": 2.6, "pcm": 2.6, "pt-BR": 2.6, "id": 2.4, "hi": 2.3, "ar": 2.2}

NUMBER = re.compile(r"\d+(?:[.,:]\d+)?")


class Message(BaseModel):
    """What a channel adapter would send."""

    channel: Channel
    text: str = ""
    title: str | None = Field(default=None, description="push only")
    value: str | None = Field(
        default=None, description="watch only: the one big number, e.g. '2-1' or '0.62'"
    )
    language: str = "en"
    audio_seconds: float | None = Field(default=None, description="voice: real duration once synthesised")


@dataclass
class LimitCheck:
    ok: bool
    reasons: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


def estimate_voice_seconds(text: str, language: str) -> float:
    """Spoken length estimate: words at the language's speaking rate, plus a short lead-in."""
    words = len(text.split())
    return round(0.4 + words / SPEECH_WORDS_PER_SECOND.get(language, 2.5), 1)


def check(msg: Message) -> LimitCheck:
    """Measure ``msg`` against its channel's hard limit."""
    reasons: list[str] = []
    metrics: dict[str, Any] = {}
    text = msg.text
    match msg.channel:
        case "sms":
            info = analyze_sms(text)
            metrics.update(
                encoding=info.encoding,
                units=info.units,
                segments=info.segments,
                single_segment_limit=info.single_segment_limit,
                non_gsm_chars="".join(info.non_gsm_chars),
            )
            if info.segments > SMS_MAX_SEGMENTS:
                reasons.append(
                    f"SMS needs {info.segments} segments ({info.units} {info.encoding} units); "
                    f"max {SMS_MAX_SEGMENTS}"
                )
        case "chat":
            metrics["chars"] = len(text)
            if len(text) > CHAT_MAX_CHARS:
                reasons.append(f"chat message is {len(text)} chars; max {CHAT_MAX_CHARS}")
        case "voice":
            seconds = (
                msg.audio_seconds
                if msg.audio_seconds is not None
                else estimate_voice_seconds(text, msg.language)
            )
            metrics.update(seconds=seconds, estimated=msg.audio_seconds is None)
            if seconds > VOICE_MAX_SECONDS:
                reasons.append(f"voice note is {seconds:.1f} s; max {VOICE_MAX_SECONDS:.0f} s")
        case "watch":
            numbers = NUMBER.findall(text)
            metrics.update(chars=len(text), numbers_in_text=len(numbers))
            if len(text) > WATCH_MAX_CHARS:
                reasons.append(f"watch text is {len(text)} chars; max {WATCH_MAX_CHARS}")
            if numbers:
                reasons.append("watch text must not contain numbers; put the one number in 'value'")
            if msg.value is not None and len(msg.value) > WATCH_MAX_VALUE_CHARS:
                reasons.append(f"watch value '{msg.value}' is longer than {WATCH_MAX_VALUE_CHARS} chars")
        case "push":
            title = msg.title or ""
            metrics.update(title_chars=len(title), body_chars=len(text))
            if not title:
                reasons.append("push needs a title")
            if len(title) > PUSH_MAX_TITLE:
                reasons.append(f"push title is {len(title)} chars; max {PUSH_MAX_TITLE}")
            if len(text) > PUSH_MAX_BODY:
                reasons.append(f"push body is {len(text)} chars; max {PUSH_MAX_BODY}")
        case "broadcast":
            pass  # overlay cues are not size-limited
    if msg.channel != "push" and not text.strip():
        reasons.append("empty message")
    return LimitCheck(ok=not reasons, reasons=reasons, metrics=metrics)
