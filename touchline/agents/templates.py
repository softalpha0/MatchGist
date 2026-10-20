"""Deterministic multilingual phrasing.

Used three ways:
  * by the Director for instant headlines (no model in the hot path);
  * by the offline model backend so the full agent pipeline runs with no keys;
  * as the Supervisor's fallback whenever a model call fails or is rejected.

Every template only interpolates facts gathered by the detector, so the
output can never contain a number that is not in the shared state.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

LANGS = ("en", "es", "fr", "pt")

T: dict[str, dict[str, dict[str, Any]]] = {
    "en": {
        "goal": {
            "headline": "GOAL — {player} {minute}",
            "fan": "{player} scores for {team}! It's {score_str}.",
            "analyst": "Shot worth {xg} xG from {distance_m} m, struck at {shot_speed_kmh} km/h. {team} now lead the chance count {team_xg}–{opponent_xg} in xG.",
            "why_low_xg": "A {xg_pct}% chance: roughly 1 in {odds} shots from there go in.",
            "why_against_run": "It came against the run of play: {opponent} had been the stronger side.",
            "why_deserved": "{team} had been building pressure, and this reward was coming.",
            "assist": "Set up by {assist} (pass difficulty {assist_difficulty}/10).",
        },
        "big_chance": {
            "headline": "BIG CHANCE — {player}",
            "fan": "{player} should have scored there! {outcome_text}.",
            "analyst": "{xg} xG chance from {distance_m} m ({outcome_text}). Chances like this go in {xg_pct}% of the time.",
        },
        "shot": {
            "headline": "{shot_speed_kmh} km/h — {player}",
            "fan": "What a strike from {player}: {shot_speed_kmh} km/h! {outcome_text}.",
            "analyst": "Ball speed {shot_speed_kmh} km/h from {distance_m} m, {xg} xG. {outcome_text}.",
        },
        "momentum_swing": {
            "headline": "MOMENTUM — {team}",
            "fan": "{team} are taking over this game right now.",
            "analyst": "{team} own {momentum_pct}% of the threat in the last {window_minutes} minutes: {final_third_passes_in_window} final-third passes and {shots_in_window} shots to {opponent_shots_in_window}.",
            "why_trailing": "They are behind, so this is the push for a way back.",
            "why_leading": "Ahead or level, this is them tightening their grip.",
        },
        "pressure_spike": {
            "headline": "PRESSING — {team}",
            "fan": "{team} are hunting the ball in packs and forcing mistakes.",
            "analyst": "{team} pressing rate up to {pressures_per_min} per minute (from {previous_per_min}), forcing {turnovers_forced} turnovers in two minutes.",
        },
        "control_shift_chaos": {
            "headline": "CHAOS",
            "fan": "This has turned wild: nobody can keep the ball for long.",
            "analyst": "Chaos index {chaos}/100: {turnovers_per_min} turnovers a minute, average move just {avg_chain} passes.",
        },
        "control_shift_control": {
            "headline": "CONTROL — {team}",
            "fan": "{team} have calmed things down and are keeping the ball.",
            "analyst": "Chaos index down to {chaos}/100: moves now average {avg_chain} passes at {pass_accuracy}% accuracy, led by {team}.",
        },
        "pass_of_note": {
            "headline": "PASS — {player} → {receiver}",
            "fan": "Lovely pass from {player} to find {receiver}!",
            "analyst": "{length_m} m pass at {ball_speed_kmh} km/h, difficulty {difficulty}/10: only a {completion_chance}% completion chance{pressure_text}.",
        },
        "sprint": {
            "headline": "{player} {speed_kmh} km/h",
            "fan": "{player} flies at {speed_kmh} km/h!",
            "analyst": "{player} sprint at {speed_kmh} km/h: sprint number {sprints}, {distance_km} km covered.",
            "why_fastest": "Fastest run of the match so far.",
        },
        "milestone_completed_passes": {
            "headline": "{player}: {value} passes",
            "fan": "{player} has completed {value} passes, running the show.",
            "analyst": "{player} reaches {value} completed passes at {pass_accuracy}% accuracy.",
        },
        "milestone_distance_km": {
            "headline": "{player}: {value} km",
            "fan": "{player} has now run {value} km. What an engine!",
            "analyst": "{player} passes {value} km covered, with {sprints} sprints.",
        },
        "card": {
            "headline": "YELLOW CARD — {player}",
            "fan": "{player} goes into the book.",
            "analyst": "Booking for {player}; {team} have committed {team_fouls} fouls.",
        },
        "half_time": {
            "headline": "HALF-TIME {home} {score_str} {away}",
            "fan": "Half-time: {home} {score_str} {away}. {standout_first} has been the standout.",
            "analyst": "HT: xG {home_xg}–{away_xg}, shots {home_shots}–{away_shots}, possession {home_possession}%–{away_possession}%.",
        },
        "full_time": {
            "headline": "FULL-TIME {home} {score_str} {away}",
            "fan": "It's all over: {home} {score_str} {away}. Player of the match: {standout_first}.",
            "analyst": "FT: xG {home_xg}–{away_xg}, shots {home_shots}–{away_shots}, possession {home_possession}%–{away_possession}%.",
        },
        "_": {
            "outcome": {"saved": "Saved", "blocked": "Blocked", "off_target": "Off target", "goal": "Goal"},
            "under_pressure": " while under pressure",
            "fav_for": "Your club: ",
            "fav_against": "Against your club: ",
            "focus": "Your player: ",
            "xg_story": "xG says {verdict}.",
            "verdict_fair": "the result is fair",
            "verdict_lucky": "{lucky} rode their luck",
        },
    },
    "es": {
        "goal": {
            "headline": "GOL — {player} {minute}",
            "fan": "¡Gol de {player} para {team}! {score_str}.",
            "analyst": "Remate de {xg} xG desde {distance_m} m a {shot_speed_kmh} km/h. {team} suma {team_xg} xG frente a {opponent_xg}.",
            "why_low_xg": "Una ocasión del {xg_pct}%: solo 1 de cada {odds} remates así acaba en gol.",
            "why_against_run": "Llegó contra la corriente: {opponent} estaba siendo mejor.",
            "why_deserved": "{team} venía apretando y el premio llegó.",
            "assist": "Asistencia de {assist} (dificultad del pase {assist_difficulty}/10).",
        },
        "big_chance": {
            "headline": "OCASIÓN CLARA — {player}",
            "fan": "¡{player} tuvo que marcar! {outcome_text}.",
            "analyst": "Ocasión de {xg} xG desde {distance_m} m ({outcome_text}). Entran el {xg_pct}% de las veces.",
        },
        "shot": {
            "headline": "{shot_speed_kmh} km/h — {player}",
            "fan": "¡Qué disparo de {player}: {shot_speed_kmh} km/h! {outcome_text}.",
            "analyst": "Velocidad del balón {shot_speed_kmh} km/h desde {distance_m} m, {xg} xG. {outcome_text}.",
        },
        "momentum_swing": {
            "headline": "DOMINIO — {team}",
            "fan": "{team} se está adueñando del partido.",
            "analyst": "{team} genera el {momentum_pct}% del peligro en los últimos {window_minutes} minutos: {final_third_passes_in_window} pases en último tercio y {shots_in_window} tiros contra {opponent_shots_in_window}.",
            "why_trailing": "Van por detrás, así que es su intento de remontada.",
            "why_leading": "Con el marcador a favor o igualado, están apretando el control.",
        },
        "pressure_spike": {
            "headline": "PRESIÓN — {team}",
            "fan": "{team} presiona en bloque y fuerza errores.",
            "analyst": "{team} sube su presión a {pressures_per_min} por minuto (antes {previous_per_min}) y fuerza {turnovers_forced} pérdidas en dos minutos.",
        },
        "control_shift_chaos": {
            "headline": "CAOS",
            "fan": "Partido loco: nadie es capaz de tener el balón.",
            "analyst": "Índice de caos {chaos}/100: {turnovers_per_min} pérdidas por minuto y jugadas de solo {avg_chain} pases.",
        },
        "control_shift_control": {
            "headline": "CONTROL — {team}",
            "fan": "{team} ha calmado el partido y tiene el balón.",
            "analyst": "El caos baja a {chaos}/100: jugadas de {avg_chain} pases con {pass_accuracy}% de acierto, lideradas por {team}.",
        },
        "pass_of_note": {
            "headline": "PASE — {player} → {receiver}",
            "fan": "¡Qué pase de {player} para encontrar a {receiver}!",
            "analyst": "Pase de {length_m} m a {ball_speed_kmh} km/h, dificultad {difficulty}/10: solo un {completion_chance}% de probabilidad de completarlo{pressure_text}.",
        },
        "sprint": {
            "headline": "{player} {speed_kmh} km/h",
            "fan": "¡{player} vuela a {speed_kmh} km/h!",
            "analyst": "Sprint de {player} a {speed_kmh} km/h: sprint número {sprints}, {distance_km} km recorridos.",
            "why_fastest": "La carrera más rápida del partido.",
        },
        "milestone_completed_passes": {
            "headline": "{player}: {value} pases",
            "fan": "{player} ya ha completado {value} pases: maneja el partido.",
            "analyst": "{player} llega a {value} pases completados con {pass_accuracy}% de acierto.",
        },
        "milestone_distance_km": {
            "headline": "{player}: {value} km",
            "fan": "{player} ya lleva {value} km. ¡Qué motor!",
            "analyst": "{player} supera los {value} km recorridos, con {sprints} sprints.",
        },
        "card": {
            "headline": "TARJETA AMARILLA — {player}",
            "fan": "Amarilla para {player}.",
            "analyst": "Amonestación a {player}; {team} acumula {team_fouls} faltas.",
        },
        "half_time": {
            "headline": "DESCANSO {home} {score_str} {away}",
            "fan": "Descanso: {home} {score_str} {away}. {standout_first} está siendo el mejor.",
            "analyst": "Descanso: xG {home_xg}–{away_xg}, tiros {home_shots}–{away_shots}, posesión {home_possession}%–{away_possession}%.",
        },
        "full_time": {
            "headline": "FINAL {home} {score_str} {away}",
            "fan": "¡Se acabó! {home} {score_str} {away}. Jugador del partido: {standout_first}.",
            "analyst": "Final: xG {home_xg}–{away_xg}, tiros {home_shots}–{away_shots}, posesión {home_possession}%–{away_possession}%.",
        },
        "_": {
            "outcome": {"saved": "Parada", "blocked": "Bloqueado", "off_target": "Fuera", "goal": "Gol"},
            "under_pressure": " bajo presión",
            "fav_for": "Tu equipo: ",
            "fav_against": "Contra tu equipo: ",
            "focus": "Tu jugador: ",
            "xg_story": "El xG dice que {verdict}.",
            "verdict_fair": "el resultado es justo",
            "verdict_lucky": "{lucky} tuvo suerte",
        },
    },
    "fr": {
        "goal": {
            "headline": "BUT — {player} {minute}",
            "fan": "But de {player} pour {team} ! {score_str}.",
            "analyst": "Frappe à {xg} xG depuis {distance_m} m, à {shot_speed_kmh} km/h. {team} totalise {team_xg} xG contre {opponent_xg}.",
            "why_low_xg": "Une occasion à {xg_pct} % : seulement 1 tir sur {odds} de cette position finit au fond.",
            "why_against_run": "Il arrive contre le cours du jeu : {opponent} dominait.",
            "why_deserved": "{team} poussait depuis un moment, la récompense est logique.",
            "assist": "Passe décisive de {assist} (difficulté {assist_difficulty}/10).",
        },
        "big_chance": {
            "headline": "GROSSE OCCASION — {player}",
            "fan": "{player} devait marquer ! {outcome_text}.",
            "analyst": "Occasion à {xg} xG depuis {distance_m} m ({outcome_text}). Elle finit au fond {xg_pct} % du temps.",
        },
        "shot": {
            "headline": "{shot_speed_kmh} km/h — {player}",
            "fan": "Quelle frappe de {player} : {shot_speed_kmh} km/h ! {outcome_text}.",
            "analyst": "Vitesse du ballon {shot_speed_kmh} km/h depuis {distance_m} m, {xg} xG. {outcome_text}.",
        },
        "momentum_swing": {
            "headline": "TEMPS FORT — {team}",
            "fan": "{team} prend le contrôle du match en ce moment.",
            "analyst": "{team} génère {momentum_pct} % du danger sur les {window_minutes} dernières minutes : {final_third_passes_in_window} passes dans le dernier tiers et {shots_in_window} tirs contre {opponent_shots_in_window}.",
            "why_trailing": "Mené au score, c'est leur poussée pour revenir.",
            "why_leading": "Devant ou à égalité, ils resserrent leur emprise.",
        },
        "pressure_spike": {
            "headline": "PRESSING — {team}",
            "fan": "{team} chasse le ballon en meute et provoque des erreurs.",
            "analyst": "{team} monte à {pressures_per_min} pressions par minute (contre {previous_per_min}) et force {turnovers_forced} pertes en deux minutes.",
        },
        "control_shift_chaos": {
            "headline": "CHAOS",
            "fan": "Match fou : personne n'arrive à garder le ballon.",
            "analyst": "Indice de chaos {chaos}/100 : {turnovers_per_min} pertes par minute, actions de {avg_chain} passes en moyenne.",
        },
        "control_shift_control": {
            "headline": "CONTRÔLE — {team}",
            "fan": "{team} a calmé le jeu et garde le ballon.",
            "analyst": "Le chaos retombe à {chaos}/100 : actions de {avg_chain} passes à {pass_accuracy} % de réussite, menées par {team}.",
        },
        "pass_of_note": {
            "headline": "PASSE — {player} → {receiver}",
            "fan": "Superbe passe de {player} pour {receiver} !",
            "analyst": "Passe de {length_m} m à {ball_speed_kmh} km/h, difficulté {difficulty}/10 : seulement {completion_chance} % de chances de réussite{pressure_text}.",
        },
        "sprint": {
            "headline": "{player} {speed_kmh} km/h",
            "fan": "{player} file à {speed_kmh} km/h !",
            "analyst": "Sprint de {player} à {speed_kmh} km/h : sprint n° {sprints}, {distance_km} km parcourus.",
            "why_fastest": "Course la plus rapide du match.",
        },
        "milestone_completed_passes": {
            "headline": "{player} : {value} passes",
            "fan": "{player} a déjà réussi {value} passes, il dirige le jeu.",
            "analyst": "{player} atteint {value} passes réussies à {pass_accuracy} %.",
        },
        "milestone_distance_km": {
            "headline": "{player} : {value} km",
            "fan": "{player} a déjà couru {value} km. Quel moteur !",
            "analyst": "{player} dépasse {value} km parcourus, avec {sprints} sprints.",
        },
        "card": {
            "headline": "CARTON JAUNE — {player}",
            "fan": "Carton jaune pour {player}.",
            "analyst": "Avertissement pour {player} ; {team} en est à {team_fouls} fautes.",
        },
        "half_time": {
            "headline": "MI-TEMPS {home} {score_str} {away}",
            "fan": "Mi-temps : {home} {score_str} {away}. {standout_first} est le meilleur jusqu'ici.",
            "analyst": "MT : xG {home_xg}–{away_xg}, tirs {home_shots}–{away_shots}, possession {home_possession} %–{away_possession} %.",
        },
        "full_time": {
            "headline": "FIN DU MATCH {home} {score_str} {away}",
            "fan": "C'est terminé : {home} {score_str} {away}. Homme du match : {standout_first}.",
            "analyst": "Fin : xG {home_xg}–{away_xg}, tirs {home_shots}–{away_shots}, possession {home_possession} %–{away_possession} %.",
        },
        "_": {
            "outcome": {"saved": "Arrêté", "blocked": "Contré", "off_target": "Non cadré", "goal": "But"},
            "under_pressure": " sous pression",
            "fav_for": "Ton club : ",
            "fav_against": "Contre ton club : ",
            "focus": "Ton joueur : ",
            "xg_story": "Selon les xG, {verdict}.",
            "verdict_fair": "le score est logique",
            "verdict_lucky": "{lucky} a eu de la chance",
        },
    },
    "pt": {
        "goal": {
            "headline": "GOL — {player} {minute}",
            "fan": "Gol de {player} para o {team}! {score_str}.",
            "analyst": "Finalização de {xg} xG a {distance_m} m, a {shot_speed_kmh} km/h. {team} soma {team_xg} xG contra {opponent_xg}.",
            "why_low_xg": "Uma chance de {xg_pct}%: só 1 em cada {odds} chutes dali vira gol.",
            "why_against_run": "Saiu contra a corrente: o {opponent} estava melhor.",
            "why_deserved": "O {team} vinha pressionando e o prêmio chegou.",
            "assist": "Assistência de {assist} (dificuldade do passe {assist_difficulty}/10).",
        },
        "big_chance": {
            "headline": "CHANCE CLARA — {player}",
            "fan": "{player} tinha que marcar! {outcome_text}.",
            "analyst": "Chance de {xg} xG a {distance_m} m ({outcome_text}). Entra em {xg_pct}% das vezes.",
        },
        "shot": {
            "headline": "{shot_speed_kmh} km/h — {player}",
            "fan": "Que chute de {player}: {shot_speed_kmh} km/h! {outcome_text}.",
            "analyst": "Velocidade da bola {shot_speed_kmh} km/h a {distance_m} m, {xg} xG. {outcome_text}.",
        },
        "momentum_swing": {
            "headline": "DOMÍNIO — {team}",
            "fan": "O {team} está tomando conta do jogo.",
            "analyst": "O {team} gera {momentum_pct}% do perigo nos últimos {window_minutes} minutos: {final_third_passes_in_window} passes no terço final e {shots_in_window} chutes contra {opponent_shots_in_window}.",
            "why_trailing": "Estão atrás no placar: é a pressão pelo empate.",
            "why_leading": "Na frente ou empatados, estão apertando o controle.",
        },
        "pressure_spike": {
            "headline": "PRESSÃO — {team}",
            "fan": "O {team} caça a bola em bloco e força erros.",
            "analyst": "O {team} sobe a pressão para {pressures_per_min} por minuto (antes {previous_per_min}) e força {turnovers_forced} perdas em dois minutos.",
        },
        "control_shift_chaos": {
            "headline": "CAOS",
            "fan": "Jogo maluco: ninguém consegue ficar com a bola.",
            "analyst": "Índice de caos {chaos}/100: {turnovers_per_min} perdas por minuto, jogadas de só {avg_chain} passes.",
        },
        "control_shift_control": {
            "headline": "CONTROLE — {team}",
            "fan": "O {team} acalmou o jogo e está com a bola.",
            "analyst": "O caos cai para {chaos}/100: jogadas de {avg_chain} passes com {pass_accuracy}% de acerto, lideradas pelo {team}.",
        },
        "pass_of_note": {
            "headline": "PASSE — {player} → {receiver}",
            "fan": "Que passe de {player} para achar {receiver}!",
            "analyst": "Passe de {length_m} m a {ball_speed_kmh} km/h, dificuldade {difficulty}/10: só {completion_chance}% de chance de completar{pressure_text}.",
        },
        "sprint": {
            "headline": "{player} {speed_kmh} km/h",
            "fan": "{player} voa a {speed_kmh} km/h!",
            "analyst": "Arrancada de {player} a {speed_kmh} km/h: sprint número {sprints}, {distance_km} km percorridos.",
            "why_fastest": "A corrida mais rápida do jogo.",
        },
        "milestone_completed_passes": {
            "headline": "{player}: {value} passes",
            "fan": "{player} já completou {value} passes e comanda o jogo.",
            "analyst": "{player} chega a {value} passes certos com {pass_accuracy}% de acerto.",
        },
        "milestone_distance_km": {
            "headline": "{player}: {value} km",
            "fan": "{player} já correu {value} km. Que fôlego!",
            "analyst": "{player} passa de {value} km percorridos, com {sprints} sprints.",
        },
        "card": {
            "headline": "CARTÃO AMARELO — {player}",
            "fan": "Amarelo para {player}.",
            "analyst": "Cartão para {player}; o {team} já soma {team_fouls} faltas.",
        },
        "half_time": {
            "headline": "INTERVALO {home} {score_str} {away}",
            "fan": "Intervalo: {home} {score_str} {away}. {standout_first} é o destaque.",
            "analyst": "Intervalo: xG {home_xg}–{away_xg}, chutes {home_shots}–{away_shots}, posse {home_possession}%–{away_possession}%.",
        },
        "full_time": {
            "headline": "FIM DE JOGO {home} {score_str} {away}",
            "fan": "Acabou: {home} {score_str} {away}. Craque do jogo: {standout_first}.",
            "analyst": "Final: xG {home_xg}–{away_xg}, chutes {home_shots}–{away_shots}, posse {home_possession}%–{away_possession}%.",
        },
        "_": {
            "outcome": {"saved": "Defesa", "blocked": "Bloqueado", "off_target": "Para fora", "goal": "Gol"},
            "under_pressure": " sob pressão",
            "fav_for": "Seu time: ",
            "fav_against": "Contra seu time: ",
            "focus": "Seu jogador: ",
            "xg_story": "O xG diz que {verdict}.",
            "verdict_fair": "o resultado é justo",
            "verdict_lucky": "o {lucky} teve sorte",
        },
    },
}


class _Safe(dict):
    def __missing__(self, key: str) -> str:
        return ""


def template_key(kind: str, facts: dict[str, Any]) -> str:
    if kind == "control_shift":
        return f"control_shift_{facts.get('state', 'chaos')}"
    if kind == "milestone":
        return f"milestone_{facts.get('milestone', 'completed_passes')}"
    return kind


def derive(facts: dict[str, Any], lang: str) -> dict[str, Any]:
    """Facts plus presentation-ready derived values (all computed, never invented)."""
    d = dict(facts)
    common = T[lang]["_"]
    score = facts.get("score")
    if isinstance(score, list) and len(score) == 2:
        d["score_str"] = f"{score[0]}–{score[1]}"
    xg = facts.get("xg")
    if isinstance(xg, (int, float)):
        d["xg"] = round(float(xg), 2)
        d["xg_pct"] = max(1, round(100 * float(xg)))
        d["odds"] = max(1, round(1 / max(float(xg), 0.01)))
    if "momentum" in facts:
        d["momentum_pct"] = round(50 + 50 * float(facts["momentum"]))
    if "outcome" in facts:
        d["outcome_text"] = common["outcome"].get(facts["outcome"], facts["outcome"])
    d["pressure_text"] = common["under_pressure"] if facts.get("under_pressure") else ""
    standout = facts.get("standout")
    if isinstance(standout, list) and standout:
        d["standout_first"] = standout[0]
    return d


def numbers_allowed(facts: dict[str, Any]) -> set[str]:
    """Every numeric token a writer may legitimately use for these facts."""
    allowed: set[str] = set()
    derived = derive(facts, "en")

    def add(v: Any) -> None:
        if isinstance(v, bool):
            return
        if isinstance(v, (int, float)):
            f = float(v)
            for s in {f"{f:g}", f"{f:.1f}", f"{f:.2f}", str(round(f)), str(int(f))}:
                allowed.add(s.rstrip("0").rstrip(".") if "." in s else s)
            if 0 < f < 1:
                allowed.add(str(round(f * 100)))
        elif isinstance(v, str):
            for tok in re.findall(r"\d+(?:\.\d+)?", v):
                add(float(tok))
        elif isinstance(v, (list, tuple)):
            for x in v:
                add(x)
        elif isinstance(v, dict):
            for x in v.values():
                add(x)

    for v in derived.values():
        add(v)
    return allowed


def pick(options: list[str], seed: str) -> str:
    h = int(hashlib.sha1(seed.encode()).hexdigest(), 16)
    return options[h % len(options)]


def render(kind: str, facts: dict[str, Any], lang: str, field: str) -> str:
    lang = lang if lang in T else "en"
    table = T[lang].get(template_key(kind, facts)) or T["en"].get(template_key(kind, facts), {})
    tpl = table.get(field)
    if not tpl:
        return ""
    return tpl.format_map(_Safe(derive(facts, lang)))


def explain(kind: str, facts: dict[str, Any], lang: str, mode: str) -> str:
    """The 'why it matters' sentence(s) for a profile."""
    lang = lang if lang in T else "en"
    key = template_key(kind, facts)
    table = T[lang].get(key, {})
    d = _Safe(derive(facts, lang))
    parts = [render(kind, facts, lang, mode)]
    if kind == "goal":
        if facts.get("low_xg_finish"):
            parts.append(table["why_low_xg"].format_map(d))
        elif facts.get("against_run_of_play"):
            parts.append(table["why_against_run"].format_map(d))
        else:
            parts.append(table["why_deserved"].format_map(d))
        if mode == "analyst" and facts.get("assist"):
            parts.append(table["assist"].format_map(d))
    elif kind == "momentum_swing":
        parts.append(table["why_trailing" if facts.get("trailing") else "why_leading"].format_map(d))
    elif kind == "sprint" and facts.get("fastest_in_match"):
        parts.append(table["why_fastest"].format_map(d))
    elif kind in ("half_time", "full_time") and mode == "analyst":
        parts.append(xg_story(facts, lang))
    return " ".join(p for p in parts if p)


def xg_story(facts: dict[str, Any], lang: str) -> str:
    common = T[lang]["_"]
    score = facts.get("score") or [0, 0]
    hx, ax = float(facts.get("home_xg", 0)), float(facts.get("away_xg", 0))
    goal_diff = score[0] - score[1]
    xg_diff = hx - ax
    if goal_diff > 0 and xg_diff < -0.5:
        verdict = common["verdict_lucky"].format(lucky=facts.get("home"))
    elif goal_diff < 0 and xg_diff > 0.5:
        verdict = common["verdict_lucky"].format(lucky=facts.get("away"))
    else:
        verdict = common["verdict_fair"]
    return common["xg_story"].format(verdict=verdict)


def prefix(lang: str, key: str) -> str:
    return T[lang if lang in T else "en"]["_"][key]
