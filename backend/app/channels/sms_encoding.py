"""GSM-7 vs UCS-2 detection and SMS segment counting (3GPP TS 23.038 / 23.040).

Never measure SMS with ``len()``:

* GSM-7 packs 160 septets into one SMS. Characters from the extension table (``^ { } \\ [ ~ ] | €``
  and form feed) take two septets each.
* A single character outside the GSM-7 alphabet (any Hindi or Arabic letter, most emoji, curly quotes)
  switches the whole message to UCS-2, which carries 70 UTF-16 code units. Emoji outside the Basic
  Multilingual Plane take two units.
* Concatenated messages spend 6 bytes per segment on the UDH header: 153 septets per GSM-7 segment,
  67 code units per UCS-2 segment. An escape pair or a surrogate pair is never split across segments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Encoding = Literal["GSM-7", "UCS-2"]

GSM7_BASIC = frozenset(
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
)
GSM7_EXTENSION = frozenset("^{}\\[~]|€\f")

GSM7_SINGLE, GSM7_MULTI = 160, 153
UCS2_SINGLE, UCS2_MULTI = 70, 67


@dataclass(frozen=True)
class SmsInfo:
    """How a text travels as SMS."""

    encoding: Encoding
    units: int  # septets for GSM-7, UTF-16 code units for UCS-2
    segments: int
    per_segment: int  # capacity per segment at this segment count
    remaining: int  # units left in the last segment
    non_gsm_chars: tuple[str, ...]  # what forced UCS-2, if anything

    @property
    def single_segment_limit(self) -> int:
        return GSM7_SINGLE if self.encoding == "GSM-7" else UCS2_SINGLE


def is_gsm7(text: str) -> bool:
    return all(c in GSM7_BASIC or c in GSM7_EXTENSION for c in text)


def non_gsm_characters(text: str) -> tuple[str, ...]:
    """Distinct characters that force UCS-2, in order of first appearance."""
    seen: dict[str, None] = {}
    for c in text:
        if c not in GSM7_BASIC and c not in GSM7_EXTENSION:
            seen.setdefault(c, None)
    return tuple(seen)


def _unit_sizes(text: str, encoding: Encoding) -> list[int]:
    """Size of each character in the encoding's units (escape and surrogate pairs count 2)."""
    if encoding == "GSM-7":
        return [2 if c in GSM7_EXTENSION else 1 for c in text]
    return [2 if ord(c) > 0xFFFF else 1 for c in text]


def _count_segments(sizes: list[int], per_segment: int) -> tuple[int, int]:
    """Greedy packing that never splits a two-unit character. Returns (segments, units in last)."""
    segments, used = 1, 0
    for s in sizes:
        if used + s > per_segment:
            segments += 1
            used = 0
        used += s
    return segments, used


def analyze_sms(text: str) -> SmsInfo:
    """Encoding, size and segment count of ``text`` sent as one (possibly concatenated) SMS."""
    encoding: Encoding = "GSM-7" if is_gsm7(text) else "UCS-2"
    sizes = _unit_sizes(text, encoding)
    units = sum(sizes)
    single, multi = (GSM7_SINGLE, GSM7_MULTI) if encoding == "GSM-7" else (UCS2_SINGLE, UCS2_MULTI)
    if units <= single:
        return SmsInfo(encoding, units, 1, single, single - units, non_gsm_characters(text))
    segments, last = _count_segments(sizes, multi)
    return SmsInfo(encoding, units, segments, multi, multi - last, non_gsm_characters(text))


def gsm_safe(text: str) -> str:
    """Swap common typographic characters for GSM-7 equivalents (curly quotes, dashes, ellipsis).

    Used by the Compressor for Latin-script languages so one stray quote doesn't cost
    90 characters of capacity. Script that genuinely needs UCS-2 (Hindi, Arabic) is left alone.
    """
    table = str.maketrans(
        {
            "‘": "'",
            "’": "'",
            "“": '"',
            "”": '"',
            "–": "-",
            "—": "-",
            "…": "...",
            " ": " ",
            "′": "'",
        }
    )
    return text.translate(table)
