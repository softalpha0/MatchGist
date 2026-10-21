"""Size model (SPEC section 6): estimated data cost of one delivery, in KB.

These are deliberately simple, documented estimates; the UI shows them as a running data meter.

| Channel   | Estimate                                         |
|-----------|--------------------------------------------------|
| sms       | 0.2 KB per segment                               |
| chat      | UTF-8 bytes + 1 KB overhead                      |
| voice     | Opus at 16 kbps: seconds x 16 / 8 KB             |
| watch     | UTF-8 bytes + 0.5 KB                             |
| push      | UTF-8 bytes (title + body) + 1 KB                |
| broadcast | 0 (overlay cues are not budgeted)                |
"""

from __future__ import annotations

from app.channels.limits import Message, estimate_voice_seconds
from app.channels.sms_encoding import analyze_sms

SMS_KB_PER_SEGMENT = 0.2
CHAT_OVERHEAD_KB = 1.0
WATCH_OVERHEAD_KB = 0.5
PUSH_OVERHEAD_KB = 1.0
VOICE_KBPS = 16


def utf8_kb(text: str) -> float:
    return len(text.encode("utf-8")) / 1024


def voice_kb(seconds: float) -> float:
    """Opus at 16 kbit/s: seconds x 16 kbit / 8 bits per byte."""
    return seconds * VOICE_KBPS / 8


def size_kb(msg: Message) -> float:
    """Estimated KB for ``msg`` on its channel, rounded to 0.01 KB."""
    match msg.channel:
        case "sms":
            kb = analyze_sms(msg.text).segments * SMS_KB_PER_SEGMENT
        case "chat":
            kb = utf8_kb(msg.text) + CHAT_OVERHEAD_KB
        case "voice":
            seconds = (
                msg.audio_seconds
                if msg.audio_seconds is not None
                else estimate_voice_seconds(msg.text, msg.language)
            )
            kb = voice_kb(seconds)
        case "watch":
            kb = utf8_kb(msg.text + (msg.value or "")) + WATCH_OVERHEAD_KB
        case "push":
            kb = utf8_kb((msg.title or "") + msg.text) + PUSH_OVERHEAD_KB
        case _:
            kb = 0.0
    return round(kb, 2)
