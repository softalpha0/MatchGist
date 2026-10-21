"""Fictional clubs and squads. Nothing here refers to a real club or player."""

from __future__ import annotations

import random

from touchline.models import Club, Player, Position, Side

CLUBS: list[Club] = [
    Club(
        id="hcf",
        name="Harbour City FC",
        short="HCF",
        colors=("#1f6feb", "#ffffff"),
        style="possession",
        strength=0.62,
    ),
    Club(
        id="nva",
        name="Northvale Athletic",
        short="NVA",
        colors=("#e5484d", "#111111"),
        style="pressing",
        strength=0.58,
    ),
    Club(
        id="kbr",
        name="Kingsbridge Rovers",
        short="KBR",
        colors=("#f5a524", "#1a1a1a"),
        style="direct",
        strength=0.52,
    ),
    Club(
        id="rmt",
        name="Redmarsh Town",
        short="RMT",
        colors=("#8e4ec6", "#f2f2f2"),
        style="balanced",
        strength=0.5,
    ),
    Club(
        id="tfw",
        name="Thornfield Wanderers",
        short="TFW",
        colors=("#12a594", "#0b1f1c"),
        style="pressing",
        strength=0.55,
    ),
    Club(
        id="esc",
        name="Eastcliff City",
        short="ESC",
        colors=("#d6409f", "#ffffff"),
        style="direct",
        strength=0.48,
    ),
]

VENUES = ["Lantern Park", "The Saltworks", "Millbrook Stadium", "Copperfield Ground", "Riverside Arena"]

FIRST = [
    "Ade",
    "Bram",
    "Caio",
    "Dario",
    "Emre",
    "Femi",
    "Gael",
    "Hugo",
    "Ilan",
    "Jonas",
    "Kofi",
    "Luka",
    "Mateo",
    "Nico",
    "Oskar",
    "Pavel",
    "Quinn",
    "Rafa",
    "Sami",
    "Tomas",
    "Ugo",
    "Vito",
    "Wale",
    "Yannis",
    "Zane",
    "Arlo",
    "Bastien",
    "Cyrus",
    "Dele",
    "Ezra",
    "Florin",
    "Idris",
    "Joaquim",
    "Kenji",
    "Lior",
]
LAST = [
    "Okonkwo-Hale",
    "Varga",
    "Lindqvist",
    "Moreau",
    "Adeyemi",
    "Castellan",
    "Brennick",
    "Sorensen",
    "Tavares",
    "Ilunga",
    "Marsh",
    "Kowalczyk",
    "Duarte",
    "Fenwick",
    "Haldane",
    "Achterberg",
    "Quist",
    "Rowntree",
    "Salvesen",
    "Taberner",
    "Umeadi",
    "Vasquez-Lowe",
    "Whitlock",
    "Yarde",
    "Zelenko",
    "Abernant",
    "Bellcote",
    "Carrow",
    "Dunmore",
    "Elstree",
    "Fairholm",
    "Garside",
    "Hollins",
    "Ivers",
    "Juxon",
    "Kettle",
    "Larkspur",
    "Mabberly",
    "Northey",
    "Oduya",
    "Pelham",
    "Renwick",
    "Stavely",
    "Thistlewood",
]

# 4-3-3: slot -> (position, default x on own half 0..1 from own goal, y 0..1)
FORMATION: list[tuple[Position, float, float]] = [
    (Position.GK, 0.04, 0.50),
    (Position.DF, 0.22, 0.15),
    (Position.DF, 0.20, 0.38),
    (Position.DF, 0.20, 0.62),
    (Position.DF, 0.22, 0.85),
    (Position.MF, 0.42, 0.30),
    (Position.MF, 0.38, 0.50),
    (Position.MF, 0.42, 0.70),
    (Position.FW, 0.62, 0.18),
    (Position.FW, 0.66, 0.50),
    (Position.FW, 0.62, 0.82),
]
SHIRT_NUMBERS = [1, 2, 4, 5, 3, 8, 6, 10, 7, 9, 11]


def get_club(club_id: str) -> Club:
    for c in CLUBS:
        if c.id == club_id:
            return c
    raise KeyError(club_id)


def build_squad(club: Club, side: Side, rng: random.Random) -> list[Player]:
    """Deterministically build an XI for ``club`` from the seeded RNG."""
    used: set[str] = set()
    players: list[Player] = []
    for slot, (pos, _, _) in enumerate(FORMATION):
        while True:
            first, last = rng.choice(FIRST), rng.choice(LAST)
            if last not in used:
                used.add(last)
                break

        def jitter(base: float = club.strength) -> float:
            return max(0.15, min(0.95, base + rng.uniform(-0.18, 0.18)))

        players.append(
            Player(
                id=f"{club.id}-{SHIRT_NUMBERS[slot]}",
                name=f"{first} {last}",
                short_name=last,
                number=SHIRT_NUMBERS[slot],
                position=pos,
                side=side,
                passing=jitter() + (0.08 if pos is Position.MF else 0),
                finishing=jitter() + (0.12 if pos is Position.FW else -0.1 if pos is Position.DF else 0),
                pace=jitter() + (0.06 if pos is Position.FW else 0),
                tackling=jitter() + (0.1 if pos is Position.DF else 0),
            )
        )
    return players
