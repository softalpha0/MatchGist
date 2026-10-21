"""Template fallbacks per moment type, language and channel, built only from moment facts.

These keep the feed alive when a model is slow, down, or keeps failing verification, and they are the
offline backend's output. Every template interpolates facts only, so a fallback can never contain a
number the Stats Engine did not produce.

Each language has, per moment type:
  * ``short``: a headline (SMS fallback, push title, overlay title)
  * ``line``: one or two sentences with the key numbers (analyst depth)
  * ``watch``: a label with no digits; the one number goes in the watch ``value``
"""

from __future__ import annotations

import unicodedata
from typing import Any

from app.channels.limits import (
    PUSH_MAX_BODY,
    PUSH_MAX_TITLE,
    WATCH_MAX_CHARS,
    Message,
    check,
)
from app.channels.sms_encoding import analyze_sms, gsm_safe

LANGUAGES = ("en", "hi", "id", "pt-BR", "ar", "pcm")
LATIN = {"en", "id", "pt-BR", "pcm"}

T: dict[str, dict[str, dict[str, str]]] = {
    "en": {
        "goal": {
            "short": "GOAL! {home_code} {score} {away_code} ({minute}') {player}",
            "line": "{player} scores for {team} ({minute}'): {home_code} {score} {away_code}. "
            "A {xg} xG chance, struck at {shot_speed_kmh} km/h.",
            "watch": "GOAL {team_code} {surname}",
        },
        "red_card": {
            "short": "RED CARD {team_code} ({minute}') {player}",
            "line": "{player} is sent off ({minute}'). {team} are down to {players_left} "
            "at {home_code} {score} {away_code}.",
            "watch": "RED CARD {surname}",
        },
        "big_chance": {
            "short": "BIG CHANCE {team_code} ({minute}') {player}",
            "line": "{player} should have scored ({minute}'): a {xg} xG chance, {outcome_text}. "
            "Still {home_code} {score} {away_code}.",
            "watch": "BIG CHANCE {surname}",
        },
        "momentum_swing": {
            "short": "{team} take over ({minute}')",
            "line": "The game has turned: {team} now hold the momentum ({minute}'), "
            "{team_shots} shots to {opponent_shots}.",
            "watch": "{team_code} on top",
        },
        "half_time": {
            "short": "HT {home_code} {score} {away_code}",
            "line": "Half-time: {home} {score} {away}. xG {home_xg} to {away_xg}, "
            "possession {home_possession}% to {away_possession}%.",
            "watch": "Half-time",
        },
        "full_time": {
            "short": "FT {home_code} {score} {away_code}",
            "line": "Full-time: {home} {score} {away}. xG {home_xg} to {away_xg}. "
            "Player of the match: {top_performer}.",
            "watch": "Full-time",
        },
        "pressure_spike": {
            "short": "{pressing_team} pressing hard ({minute}')",
            "line": "{pressing_team} are squeezing {pressed_team}: pressure on their passes "
            "is up from {pressure_index_5min_ago} to {pressure_index} ({minute}').",
            "watch": "{pressing_team} pressing",
        },
        "elite_pass": {
            "short": "Elite pass: {player} ({minute}')",
            "line": "{player} finds {receiver} with a {distance_m} m pass rated {difficulty}/10 "
            "for difficulty ({minute}').",
            "watch": "Elite pass {surname}",
        },
        "yellow_card": {
            "short": "Yellow: {player} ({minute}')",
            "line": "{player} of {team} is booked ({minute}').",
            "watch": "Yellow {surname}",
        },
        "_outcome": {"saved": "saved", "blocked": "blocked", "off_target": "off target"},
        "_more": {"bundle": "Also:"},
    },
    "hi": {
        "goal": {
            "short": "गोल! {home_code} {score} {away_code} ({minute}') {player}",
            "line": "{team} के लिए {player} का गोल ({minute}'): {home_code} {score} {away_code}। "
            "मौका {xg} xG का था, शॉट {shot_speed_kmh} किमी/घंटा।",
            "watch": "गोल {team_code} {surname}",
        },
        "red_card": {
            "short": "रेड कार्ड {team_code} ({minute}') {player}",
            "line": "{player} को बाहर भेजा गया ({minute}')। {team} अब {players_left} खिलाड़ियों के साथ, "
            "स्कोर {home_code} {score} {away_code}।",
            "watch": "रेड कार्ड {surname}",
        },
        "big_chance": {
            "short": "बड़ा मौका {team_code} ({minute}') {player}",
            "line": "{player} को गोल करना चाहिए था ({minute}'): {xg} xG का मौका, {outcome_text}।",
            "watch": "बड़ा मौका {surname}",
        },
        "momentum_swing": {
            "short": "{team} हावी ({minute}')",
            "line": "खेल पलट गया: अब {team} का दबदबा है ({minute}'), शॉट {team_shots} बनाम {opponent_shots}।",
            "watch": "{team_code} हावी",
        },
        "half_time": {
            "short": "हाफ टाइम {home_code} {score} {away_code}",
            "line": "हाफ टाइम: {home} {score} {away}। xG {home_xg} बनाम {away_xg}, कब्ज़ा "
            "{home_possession}% बनाम {away_possession}%।",
            "watch": "हाफ टाइम",
        },
        "full_time": {
            "short": "फुल टाइम {home_code} {score} {away_code}",
            "line": "मैच खत्म: {home} {score} {away}। xG {home_xg} बनाम {away_xg}। "
            "सर्वश्रेष्ठ खिलाड़ी: {top_performer}।",
            "watch": "फुल टाइम",
        },
        "pressure_spike": {
            "short": "{pressing_team} का ज़ोरदार दबाव ({minute}')",
            "line": "{pressing_team} ने {pressed_team} को घेरा: पास पर दबाव "
            "{pressure_index_5min_ago} से बढ़कर {pressure_index} ({minute}')।",
            "watch": "{pressing_team} का दबाव",
        },
        "elite_pass": {
            "short": "शानदार पास: {player} ({minute}')",
            "line": "{player} ने {receiver} को {distance_m} मीटर का पास दिया, कठिनाई "
            "{difficulty}/10 ({minute}')।",
            "watch": "शानदार पास {surname}",
        },
        "yellow_card": {
            "short": "पीला कार्ड: {player} ({minute}')",
            "line": "{team} के {player} को पीला कार्ड ({minute}')।",
            "watch": "पीला कार्ड {surname}",
        },
        "_outcome": {"saved": "गोलकीपर ने बचाया", "blocked": "रोक दिया गया", "off_target": "निशाना चूका"},
        "_more": {"bundle": "साथ ही:"},
    },
    "id": {
        "goal": {
            "short": "GOL! {home_code} {score} {away_code} ({minute}') {player}",
            "line": "{player} mencetak gol untuk {team} ({minute}'): {home_code} {score} {away_code}. "
            "Peluang {xg} xG, tendangan {shot_speed_kmh} km/jam.",
            "watch": "GOL {team_code} {surname}",
        },
        "red_card": {
            "short": "KARTU MERAH {team_code} ({minute}') {player}",
            "line": "{player} diusir ({minute}'). {team} tinggal {players_left} pemain, "
            "skor {home_code} {score} {away_code}.",
            "watch": "KARTU MERAH {surname}",
        },
        "big_chance": {
            "short": "PELUANG EMAS {team_code} ({minute}') {player}",
            "line": "{player} seharusnya mencetak gol ({minute}'): peluang {xg} xG, {outcome_text}.",
            "watch": "PELUANG EMAS {surname}",
        },
        "momentum_swing": {
            "short": "{team} kuasai laga ({minute}')",
            "line": "Laga berbalik: {team} kini pegang momentum ({minute}'), tembakan "
            "{team_shots} lawan {opponent_shots}.",
            "watch": "{team_code} menguasai",
        },
        "half_time": {
            "short": "BABAK I {home_code} {score} {away_code}",
            "line": "Turun minum: {home} {score} {away}. xG {home_xg} lawan {away_xg}, "
            "penguasaan bola {home_possession}% lawan {away_possession}%.",
            "watch": "Turun minum",
        },
        "full_time": {
            "short": "SELESAI {home_code} {score} {away_code}",
            "line": "Laga usai: {home} {score} {away}. xG {home_xg} lawan {away_xg}. "
            "Pemain terbaik: {top_performer}.",
            "watch": "Laga usai",
        },
        "pressure_spike": {
            "short": "{pressing_team} menekan ketat ({minute}')",
            "line": "{pressing_team} menekan {pressed_team}: tekanan pada umpan naik dari "
            "{pressure_index_5min_ago} ke {pressure_index} ({minute}').",
            "watch": "{pressing_team} menekan",
        },
        "elite_pass": {
            "short": "Umpan kelas atas: {player} ({minute}')",
            "line": "{player} mengirim umpan {distance_m} m ke {receiver}, kesulitan "
            "{difficulty}/10 ({minute}').",
            "watch": "Umpan top {surname}",
        },
        "yellow_card": {
            "short": "Kartu kuning: {player} ({minute}')",
            "line": "{player} ({team}) dapat kartu kuning ({minute}').",
            "watch": "Kartu kuning {surname}",
        },
        "_outcome": {"saved": "ditepis kiper", "blocked": "diblok", "off_target": "melenceng"},
        "_more": {"bundle": "Juga:"},
    },
    "pt-BR": {
        "goal": {
            "short": "GOL! {home_code} {score} {away_code} ({minute}') {player}",
            "line": "{player} marca para o {team} ({minute}'): {home_code} {score} {away_code}. "
            "Chance de {xg} xG, chute a {shot_speed_kmh} km/h.",
            "watch": "GOL {team_code} {surname}",
        },
        "red_card": {
            "short": "VERMELHO {team_code} ({minute}') {player}",
            "line": "{player} é expulso ({minute}'). O {team} fica com {players_left}, "
            "placar {home_code} {score} {away_code}.",
            "watch": "VERMELHO {surname}",
        },
        "big_chance": {
            "short": "CHANCE CLARA {team_code} ({minute}') {player}",
            "line": "{player} tinha que marcar ({minute}'): chance de {xg} xG, {outcome_text}.",
            "watch": "CHANCE CLARA {surname}",
        },
        "momentum_swing": {
            "short": "{team} domina ({minute}')",
            "line": "O jogo virou: agora o {team} manda na partida ({minute}'), "
            "{team_shots} finalizações contra {opponent_shots}.",
            "watch": "{team_code} domina",
        },
        "half_time": {
            "short": "INTERVALO {home_code} {score} {away_code}",
            "line": "Intervalo: {home} {score} {away}. xG {home_xg} a {away_xg}, "
            "posse {home_possession}% a {away_possession}%.",
            "watch": "Intervalo",
        },
        "full_time": {
            "short": "FIM {home_code} {score} {away_code}",
            "line": "Fim de jogo: {home} {score} {away}. xG {home_xg} a {away_xg}. "
            "Craque do jogo: {top_performer}.",
            "watch": "Fim de jogo",
        },
        "pressure_spike": {
            "short": "{pressing_team} pressiona forte ({minute}')",
            "line": "O {pressing_team} sufoca o {pressed_team}: pressão nos passes subiu de "
            "{pressure_index_5min_ago} para {pressure_index} ({minute}').",
            "watch": "{pressing_team} pressiona",
        },
        "elite_pass": {
            "short": "Passe de craque: {player} ({minute}')",
            "line": "{player} acha {receiver} com um passe de {distance_m} m, dificuldade "
            "{difficulty}/10 ({minute}').",
            "watch": "Passe de craque {surname}",
        },
        "yellow_card": {
            "short": "Amarelo: {player} ({minute}')",
            "line": "{player} ({team}) leva amarelo ({minute}').",
            "watch": "Amarelo {surname}",
        },
        "_outcome": {"saved": "o goleiro defendeu", "blocked": "bloqueado", "off_target": "para fora"},
        "_more": {"bundle": "Também:"},
    },
    "ar": {
        "goal": {
            "short": "هدف! {home_code} {score} {away_code} ({minute}') {player}",
            "line": "{player} يسجل لـ{team} ({minute}'): {home_code} {score} {away_code}. "
            "فرصة بقيمة {xg} xG، وسرعة التسديدة {shot_speed_kmh} كم/س.",
            "watch": "هدف {team_code} {surname}",
        },
        "red_card": {
            "short": "بطاقة حمراء {team_code} ({minute}') {player}",
            "line": "طرد {player} ({minute}'). {team} يكمل بـ{players_left} لاعبين، "
            "والنتيجة {home_code} {score} {away_code}.",
            "watch": "بطاقة حمراء {surname}",
        },
        "big_chance": {
            "short": "فرصة محققة {team_code} ({minute}') {player}",
            "line": "كان على {player} أن يسجل ({minute}'): فرصة بقيمة {xg} xG، {outcome_text}.",
            "watch": "فرصة محققة {surname}",
        },
        "momentum_swing": {
            "short": "{team} يسيطر ({minute}')",
            "line": "انقلبت المباراة: {team} يفرض سيطرته الآن ({minute}')، {team_shots} "
            "تسديدات مقابل {opponent_shots}.",
            "watch": "{team_code} يسيطر",
        },
        "half_time": {
            "short": "الشوط الأول {home_code} {score} {away_code}",
            "line": "بين الشوطين: {home} {score} {away}. xG {home_xg} مقابل {away_xg}، "
            "الاستحواذ {home_possession}% مقابل {away_possession}%.",
            "watch": "بين الشوطين",
        },
        "full_time": {
            "short": "النهاية {home_code} {score} {away_code}",
            "line": "نهاية المباراة: {home} {score} {away}. xG {home_xg} مقابل {away_xg}. "
            "أفضل لاعب: {top_performer}.",
            "watch": "نهاية المباراة",
        },
        "pressure_spike": {
            "short": "ضغط قوي من {pressing_team} ({minute}')",
            "line": "{pressing_team} يضغط على {pressed_team}: الضغط على تمريراته ارتفع من "
            "{pressure_index_5min_ago} إلى {pressure_index} ({minute}').",
            "watch": "ضغط {pressing_team}",
        },
        "elite_pass": {
            "short": "تمريرة مميزة: {player} ({minute}')",
            "line": "{player} يمرر إلى {receiver} كرة لمسافة {distance_m} م، صعوبتها "
            "{difficulty}/10 ({minute}').",
            "watch": "تمريرة مميزة {surname}",
        },
        "yellow_card": {
            "short": "بطاقة صفراء: {player} ({minute}')",
            "line": "إنذار لـ{player} من {team} ({minute}').",
            "watch": "إنذار {surname}",
        },
        "_outcome": {"saved": "تصدى لها الحارس", "blocked": "صُدّت", "off_target": "خارج المرمى"},
        "_more": {"bundle": "وأيضًا:"},
    },
    "pcm": {
        "goal": {
            "short": "GOAL! {home_code} {score} {away_code} ({minute}') {player}",
            "line": "{player} don score for {team} ({minute}'): {home_code} {score} {away_code}. "
            "Na {xg} xG chance, the shot fly {shot_speed_kmh} km/h.",
            "watch": "GOAL {team_code} {surname}",
        },
        "red_card": {
            "short": "RED CARD {team_code} ({minute}') {player}",
            "line": "Ref don send {player} commot ({minute}'). {team} remain {players_left} players, "
            "score na {home_code} {score} {away_code}.",
            "watch": "RED CARD {surname}",
        },
        "big_chance": {
            "short": "BIG CHANCE {team_code} ({minute}') {player}",
            "line": "{player} for don score am ({minute}'): {xg} xG chance, {outcome_text}.",
            "watch": "BIG CHANCE {surname}",
        },
        "momentum_swing": {
            "short": "{team} don take over ({minute}')",
            "line": "Match don turn: {team} dey control am now ({minute}'), {team_shots} shots "
            "to {opponent_shots}.",
            "watch": "{team_code} dey control",
        },
        "half_time": {
            "short": "HALF TIME {home_code} {score} {away_code}",
            "line": "Half time: {home} {score} {away}. xG {home_xg} to {away_xg}, ball possession "
            "{home_possession}% to {away_possession}%.",
            "watch": "Half time",
        },
        "full_time": {
            "short": "FULL TIME {home_code} {score} {away_code}",
            "line": "Match don end: {home} {score} {away}. xG {home_xg} to {away_xg}. "
            "Best player na {top_performer}.",
            "watch": "Full time",
        },
        "pressure_spike": {
            "short": "{pressing_team} dey press well well ({minute}')",
            "line": "{pressing_team} dey hold {pressed_team} for neck: pressure on their passes "
            "don rise from {pressure_index_5min_ago} to {pressure_index} ({minute}').",
            "watch": "{pressing_team} dey press",
        },
        "elite_pass": {
            "short": "Correct pass: {player} ({minute}')",
            "line": "{player} find {receiver} with {distance_m} m pass, difficulty "
            "{difficulty}/10 ({minute}').",
            "watch": "Correct pass {surname}",
        },
        "yellow_card": {
            "short": "Yellow card: {player} ({minute}')",
            "line": "Ref book {player} of {team} ({minute}').",
            "watch": "Yellow card {surname}",
        },
        "_outcome": {"saved": "keeper save am", "blocked": "dem block am", "off_target": "e no enter"},
        "_more": {"bundle": "Plus:"},
    },
}

# The one number a watch glance shows, per moment type.
WATCH_VALUE = {
    "goal": "score",
    "red_card": "score",
    "half_time": "score",
    "full_time": "score",
    "big_chance": "xg",
    "momentum_swing": "momentum_now",
    "pressure_spike": "pressure_index",
    "elite_pass": "difficulty",
    "yellow_card": "minute",
}


class _Safe(dict):
    def __missing__(self, key: str) -> str:
        return ""


def _lang(language: str) -> str:
    return language if language in T else "en"


def derive(facts: dict[str, Any], language: str) -> dict[str, Any]:
    """Facts plus display helpers (all derived from facts, never invented)."""
    d = dict(facts)
    lang = _lang(language)
    player = facts.get("player")
    if isinstance(player, str) and player:
        d["surname"] = player.split()[-1]
    if "outcome" in facts:
        d["outcome_text"] = T[lang]["_outcome"].get(facts["outcome"], facts["outcome"])
    return d


def render(mtype: str, facts: dict[str, Any], language: str, form: str) -> str:
    """One template form (``short``, ``line`` or ``watch``) in ``language``, with whitespace tidied."""
    lang = _lang(language)
    tpl = T[lang].get(mtype, {}).get(form) or T["en"].get(mtype, {}).get(form, "")
    return " ".join(tpl.format_map(_Safe(derive(facts, lang))).split())


def first_sentence(text: str) -> str:
    for stop in ("। ", ". ", "، "):  # Devanagari danda, Latin full stop, Arabic comma ends a clause
        if stop in text:
            return text.split(stop, 1)[0].rstrip() + ("।" if stop == "। " else "." if stop == ". " else "")
    return text


def strip_accents(text: str) -> str:
    """Latin-script text squeezed into GSM-7: drop diacritics GSM-7 cannot carry (ç->c, ã->a)."""
    out = []
    for ch in gsm_safe(text):
        if analyze_sms(ch).encoding == "GSM-7":
            out.append(ch)
            continue
        base = unicodedata.normalize("NFKD", ch)
        stripped = "".join(c for c in base if not unicodedata.combining(c))
        out.append(stripped if stripped and analyze_sms(stripped).encoding == "GSM-7" else ch)
    return "".join(out)


def watch_value(mtype: str, facts: dict[str, Any]) -> str | None:
    key = WATCH_VALUE.get(mtype)
    if not key or facts.get(key) is None:
        return None
    v = facts[key]
    return f"{v}'" if key == "minute" else str(v)


def fit_text(text: str, channel: str, language: str, max_segments: int = 1) -> str:
    """Last-resort deterministic fit: trim whole words until ``text`` meets the channel limit."""

    def ok(t: str) -> bool:
        if channel == "sms":
            return analyze_sms(t).segments <= max_segments
        return check(Message(channel=channel, text=t, language=language, title="x")).ok

    words = text.split()
    while words and not ok(" ".join(words)):
        words.pop()
    return " ".join(words) or text[:20]


def compose(
    mtype: str, facts: dict[str, Any], language: str, channel: str, depth: str, max_segments: int = 1
) -> Message:
    """Best template message for one moment that fits the channel: the fallback's final answer."""
    line = render(mtype, facts, language, "line")
    short = render(mtype, facts, language, "short")
    candidates = [line, first_sentence(line), short] if depth == "analyst" else [first_sentence(line), short]
    if channel == "watch":
        text = render(mtype, facts, language, "watch")
        text = "".join(c for c in text if not c.isdigit()).strip()[:WATCH_MAX_CHARS]
        return Message(channel="watch", text=text, value=watch_value(mtype, facts), language=language)
    if channel == "push":
        body = next((c for c in candidates if len(c) <= PUSH_MAX_BODY), fit_text(line, "push", language))
        return Message(channel="push", title=short[:PUSH_MAX_TITLE], text=body, language=language)
    if channel == "sms":
        for c in candidates:
            for variant in (gsm_safe(c), strip_accents(c)) if _lang(language) in LATIN else (c,):
                if analyze_sms(variant).segments <= max_segments:
                    return Message(channel="sms", text=variant, language=language)
        return Message(channel="sms", text=fit_text(short, "sms", language, max_segments), language=language)
    for c in candidates:
        if check(Message(channel=channel, text=c, language=language)).ok:
            return Message(channel=channel, text=c, language=language)
    return Message(channel=channel, text=fit_text(short, channel, language), language=language)
