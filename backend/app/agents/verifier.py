"""Verifier: deterministic gate every delivery passes before it is sent.

1. Every number in the output exists in the moment facts or the Match State snapshot (with rounding
   tolerance), so no model can invent a statistic. Devanagari and Arabic-Indic digits are normalised
   first, so a translated number is checked like any other.
2. The channel's hard limit holds (SMS measured in real GSM-7/UCS-2 segments), within the segment
   allowance the Budget Guard gave this delivery.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from app.channels.limits import Message, check
from app.channels.sms_encoding import analyze_sms

NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
SCALES = {"10", "100"}  # rating denominators such as "8/10"


@dataclass
class Verdict:
    ok: bool
    reasons: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


def normalise_digits(text: str) -> str:
    """Map any Unicode decimal digit (e.g. Devanagari ५, Arabic-Indic ٥) to ASCII."""
    out = []
    for ch in text:
        if ch.isdigit() and not ch.isascii():
            try:
                out.append(str(unicodedata.decimal(ch)))
                continue
            except ValueError:
                pass
        out.append(ch)
    return "".join(out)


def allowed_numbers(*sources: Any) -> set[float]:
    """Every number found anywhere in the given facts / snapshot structures."""
    found: set[float] = set()

    def walk(v: Any) -> None:
        if isinstance(v, bool) or v is None:
            return
        if isinstance(v, (int, float)):
            found.add(float(v))
            if 0 < v < 1:
                found.add(round(float(v) * 100))  # 0.62 may be written as 62%
        elif isinstance(v, str):
            for tok in NUMBER.findall(normalise_digits(v)):
                found.add(float(tok.replace(",", ".")))
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, (list, tuple)):
            for x in v:
                walk(x)

    for s in sources:
        walk(s)
    found.update(float(s) for s in SCALES)
    return found


def _supported(value: float, allowed: set[float]) -> bool:
    # rounding tolerance: 0.62 -> 0.6, 103.4 -> 103
    return any(abs(value - a) <= max(0.051, 0.006 * abs(a)) for a in allowed)


def unsupported_numbers(text: str, allowed: set[float]) -> list[str]:
    bad = []
    for tok in NUMBER.findall(normalise_digits(text)):
        if not _supported(float(tok.replace(",", ".")), allowed):
            bad.append(tok)
    return bad


def verify(
    msg: Message, facts: dict[str, Any], snapshot: dict[str, Any] | None = None, max_segments: int = 2
) -> Verdict:
    """Check numbers and limits. ``max_segments`` is the Budget Guard's SMS allowance for this delivery."""
    reasons: list[str] = []
    allowed = allowed_numbers(facts, snapshot or {})
    text = " ".join(x for x in (msg.title, msg.text, msg.value) if x)
    bad = unsupported_numbers(text, allowed)
    if bad:
        reasons.append(f"numbers not in Match State: {', '.join(bad[:5])}")
    limit = check(msg)
    reasons.extend(limit.reasons)
    metrics = dict(limit.metrics)
    if msg.channel == "sms":
        info = analyze_sms(msg.text)
        if info.segments > max_segments and not limit.reasons:
            reasons.append(
                f"SMS is {info.segments} segments ({info.units} {info.encoding} units, "
                f"{info.single_segment_limit}-char segments); allowance is {max_segments}"
            )
    return Verdict(ok=not reasons, reasons=reasons, metrics=metrics)
