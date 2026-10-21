"""CLI: ``python -m app.simulator --seed 42 --storyline comeback --out ../matches/m001.jsonl``."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from app.simulator.engine import generate_match, write_jsonl


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="python -m app.simulator", description="Generate a synthetic match."
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--storyline", default="none", choices=["none", "comeback", "red_card", "late_drama"])
    parser.add_argument("--match-id", default=None)
    parser.add_argument(
        "--out", type=Path, default=None, help="JSONL path (default: ../matches/<match_id>.jsonl)"
    )
    args = parser.parse_args(argv)

    match = generate_match(args.seed, args.storyline, match_id=args.match_id)
    out = args.out or Path(__file__).resolve().parents[3] / "matches" / f"{match.match_id}.jsonl"
    write_jsonl(match, out)

    counts = Counter(e.type for e in match.events)
    h, a = match.final_score
    goals = [
        f"{e.match_clock} {e.team_id} {e.player_id}"
        for e in match.events
        if e.type == "shot" and e.outcome == "goal"
    ]
    print(f"{match.home.name} {h}-{a} {match.away.name}  ({match.storyline}, sim seed {match.sim_seed})")
    print(f"{len(match.events)} events -> {out}")
    print("by type: " + ", ".join(f"{k} {v}" for k, v in counts.most_common()))
    print("goals: " + ("; ".join(goals) or "none"))


if __name__ == "__main__":
    main()
