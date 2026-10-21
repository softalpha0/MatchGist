import pytest

from app.channels.limits import Message, check, estimate_voice_seconds
from app.channels.sizing import size_kb
from app.channels.sms_encoding import analyze_sms, gsm_safe, is_gsm7

# ------------------------------------------------------------------ encoding detection


def test_pure_gsm7_text():
    info = analyze_sms("GOAL! RIV 2-1 NOR (67') Lysenko-Vale. Counter in 11 seconds @ 31 km/h.")
    assert info.encoding == "GSM-7" and info.segments == 1 and not info.non_gsm_chars


def test_gsm7_accents_in_the_basic_table_stay_gsm7():
    assert is_gsm7("Müller é Ñu ù à øre ÄÖÜ ß £ ¥ ¿¡")
    assert not is_gsm7("ú")  # acute u is not in GSM-7, only grave ù


def test_one_non_gsm_character_switches_whole_message():
    info = analyze_sms("GOAL for Riverside ’")  # one curly apostrophe
    assert info.encoding == "UCS-2"
    assert info.non_gsm_chars == ("’",)
    assert info.single_segment_limit == 70


def test_portuguese_cedilla_and_tilde_force_ucs2():
    # ç, ã, ê are not in GSM-7: Brazilian Portuguese often costs UCS-2 unless rewritten
    assert analyze_sms("Gol do Riverside, que virada! Emoção").encoding == "UCS-2"
    assert set(analyze_sms("ação três").non_gsm_chars) == {"ç", "ã", "ê"}


def test_hindi_is_ucs2():
    info = analyze_sms("गोल! रिवरसाइड 2-1")
    assert info.encoding == "UCS-2" and info.units == len("गोल! रिवरसाइड 2-1")


def test_arabic_is_ucs2():
    assert analyze_sms("هدف! ريفرسايد 2-1").encoding == "UCS-2"


def test_emoji_is_ucs2_and_counts_two_units():
    info = analyze_sms("GOAL ⚽")  # U+26BD is in the BMP: one unit
    assert info.encoding == "UCS-2" and info.units == 6
    info = analyze_sms("GOAL 🔥")  # U+1F525 is outside the BMP: a surrogate pair
    assert info.units == 7


def test_extension_characters_cost_two_septets():
    info = analyze_sms("[2-1] €5 {x}")
    assert info.encoding == "GSM-7"
    assert info.units == len("[2-1] €5 {x}") + 5


# ------------------------------------------------------------------ boundaries


@pytest.mark.parametrize(("n", "segments"), [(160, 1), (161, 2), (306, 2), (307, 3), (459, 3), (460, 4)])
def test_gsm7_boundaries(n, segments):
    info = analyze_sms("a" * n)
    assert (info.encoding, info.segments) == ("GSM-7", segments)


@pytest.mark.parametrize(("n", "segments"), [(70, 1), (71, 2), (134, 2), (135, 3), (201, 3), (202, 4)])
def test_ucs2_boundaries(n, segments):
    info = analyze_sms("ग" * n)
    assert (info.encoding, info.segments) == ("UCS-2", segments)


def test_multi_segment_capacity_is_153_and_67():
    assert analyze_sms("a" * 161).per_segment == 153
    assert analyze_sms("ग" * 71).per_segment == 67
    assert analyze_sms("a" * 160).per_segment == 160
    assert analyze_sms("a" * 161).remaining == 153 - 8


def test_escape_pair_is_not_split_across_segments():
    # 152 plain chars then '€' (2 septets): 154 > 153, so '€' moves whole to segment 2
    info = analyze_sms("a" * 152 + "€" + "a" * 10)
    assert info.segments == 2 and info.remaining == 153 - 12


def test_surrogate_pair_is_not_split_across_segments():
    info = analyze_sms("ग" * 66 + "🔥" + "ग" * 10)  # 66 + 2 > 67 at the boundary
    assert info.segments == 2 and info.remaining == 67 - 12


def test_gsm_safe_rewrites_typography_only():
    assert gsm_safe("It’s “over” — 2–1…") == 'It\'s "over" - 2-1...'
    assert is_gsm7(gsm_safe("It’s 2–1"))
    assert gsm_safe("गोल") == "गोल"


# ------------------------------------------------------------------ channel limits


def test_sms_limit_checks_segments_not_length():
    assert check(Message(channel="sms", text="a" * 300)).ok  # 2 segments
    bad = check(Message(channel="sms", text="a" * 307))
    assert not bad.ok and "3 segments" in bad.reasons[0]
    hindi = check(Message(channel="sms", text="ग" * 72, language="hi"))
    assert hindi.ok and hindi.metrics["segments"] == 2 and hindi.metrics["encoding"] == "UCS-2"


def test_chat_limit():
    assert check(Message(channel="chat", text="x" * 280)).ok
    assert not check(Message(channel="chat", text="x" * 281)).ok


def test_voice_limit_uses_real_duration_when_known():
    long_text = " ".join(["word"] * 60)
    assert not check(Message(channel="voice", text=long_text)).ok
    assert check(Message(channel="voice", text=long_text, audio_seconds=12.0)).ok
    assert estimate_voice_seconds("one two three four five", "en") == pytest.approx(2.3)


def test_watch_limit_text_and_one_number():
    assert check(Message(channel="watch", text="Riverside score late", value="2-1")).ok
    r = check(Message(channel="watch", text="Riverside 2-1 up", value="2-1"))
    assert not r.ok and "numbers" in r.reasons[0]
    assert not check(Message(channel="watch", text="x" * 41)).ok


def test_push_limit():
    assert check(Message(channel="push", title="GOAL Riverside", text="x" * 100)).ok
    assert not check(Message(channel="push", title="t" * 51, text="ok")).ok
    assert not check(Message(channel="push", title="ok", text="x" * 101)).ok
    assert not check(Message(channel="push", text="no title")).ok


def test_empty_message_rejected():
    assert not check(Message(channel="sms", text="  ")).ok


# ------------------------------------------------------------------ size model


def test_sizes_follow_spec():
    assert size_kb(Message(channel="sms", text="a" * 160)) == 0.2
    assert size_kb(Message(channel="sms", text="a" * 161)) == 0.4
    assert size_kb(Message(channel="sms", text="ग" * 71)) == 0.4
    assert size_kb(Message(channel="voice", text="", audio_seconds=12)) == 24.0
    assert size_kb(Message(channel="chat", text="x" * 1024)) == 2.0
    assert size_kb(Message(channel="watch", text="")) == 0.5
    assert size_kb(Message(channel="push", title="", text="")) == 1.0
    assert size_kb(Message(channel="broadcast", text="cue")) == 0.0


def test_worked_example_jakarta():
    """SPEC 6.1: 4 single-segment pings + a 3-segment digest = 1.4 KB of a 1,024 KB budget."""
    ping = size_kb(Message(channel="sms", text="GOL! RIV 2-1 NOR (67') Lysenko-Vale."))
    digest = size_kb(Message(channel="sms", text="x" * 400))
    assert ping == 0.2 and digest == 0.6
    assert round(4 * ping + digest, 2) == 1.4
