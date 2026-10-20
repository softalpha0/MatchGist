"""Command line entry point: ``touchline serve`` or ``touchline simulate``."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="touchline")
    sub = parser.add_subparsers(dest="cmd", required=True)
    serve = sub.add_parser("serve", help="run the web app")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8000)
    sim = sub.add_parser(
        "simulate", help="run one match through the pipeline and print the cues as JSON lines"
    )
    sim.add_argument("--seed", type=int, default=7)
    sim.add_argument("--mode", default="analyst", choices=["analyst", "fan"])
    sim.add_argument("--lang", default="en", choices=["en", "es", "fr", "pt"])
    sim.add_argument("--events", action="store_true", help="print the raw synthetic events instead of cues")
    args = parser.parse_args(argv)

    if args.cmd == "serve":
        import uvicorn

        uvicorn.run("touchline.server.app:app", host=args.host, port=args.port)
    elif args.cmd == "simulate":
        asyncio.run(_simulate(args))


async def _simulate(args: argparse.Namespace) -> None:
    from touchline.agents.pipeline import MatchPipeline
    from touchline.config import get_settings
    from touchline.models import Profile
    from touchline.sim.engine import MatchEngine

    engine = MatchEngine(args.seed)
    if args.events:
        for _, events in engine.run():
            for e in events:
                sys.stdout.write(e.model_dump_json(exclude_none=True) + "\n")
        return
    pipe = MatchPipeline(engine.meta, Profile(mode=args.mode, language=args.lang), get_settings())
    for frame, events in engine.run():
        out = await pipe.tick([frame], [e.model_dump(mode="json") for e in events])
        for cue in out.cues:
            update = await pipe.enrich(pipe.insights[cue.insight_id])
            if update:
                cue.why, cue.revision = update.why, 1
            sys.stdout.write(json.dumps(cue.model_dump(mode="json"), ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
