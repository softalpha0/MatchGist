"""Azure AI Speech text-to-speech for voice notes, with a text fallback.

Uses the Speech REST API (no SDK) and asks for Ogg/Opus at 16 kHz, then reports the *real* duration (read from
the last Ogg page's granule position) and the real size. Without ``AZURE_SPEECH_KEY`` and
``AZURE_SPEECH_REGION``, or if the call fails, the voice note is delivered as text and marked as a fallback.

Voices (verify in the Azure portal's Voice Gallery before the demo): Nigerian Pidgin has no dedicated
neural voice we could confirm, so ``pcm`` is read by the Nigerian English voice and labelled as such.
"""

from __future__ import annotations

import logging
import os
import struct
from dataclasses import dataclass
from html import escape

import httpx

log = logging.getLogger(__name__)

VOICES = {
    "en": ("en-GB", "en-GB-SoniaNeural"),
    "hi": ("hi-IN", "hi-IN-SwaraNeural"),
    "id": ("id-ID", "id-ID-GadisNeural"),
    "pt-BR": ("pt-BR", "pt-BR-FranciscaNeural"),
    "ar": ("ar-AE", "ar-AE-FatimaNeural"),
    "pcm": ("en-NG", "en-NG-EzinneNeural"),  # no pcm voice: Nigerian English voice reads the Pidgin text
}
OUTPUT_FORMAT = "ogg-16khz-16bit-mono-opus"
OPUS_GRANULE_RATE = 48_000  # Ogg/Opus granule positions always count 48 kHz samples

AUDIO_STORE: dict[str, bytes] = {}  # delivery_id -> audio bytes (in memory; fine for a demo)


@dataclass
class VoiceNote:
    audio: bytes | None
    seconds: float | None
    size_kb: float | None
    voice: str | None
    note: str


def configured() -> bool:
    return bool(os.getenv("AZURE_SPEECH_KEY") and os.getenv("AZURE_SPEECH_REGION"))


def ogg_duration_seconds(data: bytes) -> float | None:
    """Duration of an Ogg/Opus stream from the granule position of its last page."""
    idx = data.rfind(b"OggS")
    if idx < 0 or idx + 14 > len(data):
        return None
    (granule,) = struct.unpack_from("<q", data, idx + 6)
    pre_skip = 0
    head = data.find(b"OpusHead")
    if head >= 0 and head + 12 <= len(data):
        (pre_skip,) = struct.unpack_from("<H", data, head + 10)
    return round(max(granule - pre_skip, 0) / OPUS_GRANULE_RATE, 2)


def ssml(text: str, language: str) -> str:
    locale, voice = VOICES.get(language, VOICES["en"])
    return (
        f'<speak version="1.0" xml:lang="{locale}"><voice name="{voice}">'
        f'<prosody rate="+5%">{escape(text)}</prosody></voice></speak>'
    )


async def synthesize(text: str, language: str, timeout_s: float = 10.0) -> VoiceNote:
    """Text to an Ogg/Opus voice note. Never raises: failures come back as a text fallback."""
    locale, voice = VOICES.get(language, VOICES["en"])
    label = voice + (" (reading Nigerian Pidgin)" if language == "pcm" else "")
    if not configured():
        return VoiceNote(None, None, None, label, "speech not configured: sent as text")
    region, key = os.environ["AZURE_SPEECH_REGION"], os.environ["AZURE_SPEECH_KEY"]
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": OUTPUT_FORMAT,
        "User-Agent": "matchgist",
    }
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            r = await client.post(url, content=ssml(text, language).encode("utf-8"), headers=headers)
        r.raise_for_status()
    except Exception as exc:  # network, auth, quota: the fan still gets the words
        log.warning("speech synthesis failed: %s", exc)
        return VoiceNote(None, None, None, label, f"speech failed ({type(exc).__name__}): sent as text")
    audio = r.content
    return VoiceNote(audio, ogg_duration_seconds(audio), round(len(audio) / 1024, 2), label, "synthesised")
