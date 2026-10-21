"""FastAPI app: matches, the live SSE stream, match state and fan personas."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, get_args

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app import __version__
from app.fans.profiles import FanProfile, load_fans
from app.runtime import MatchRuntime
from app.simulator.engine import generate_match
from app.simulator.schema import Match, Storyline
from app.state.match_state import MatchState

log = logging.getLogger(__name__)

DEMO_SEED = 42
DEMO_SPEED = 60.0
KEEPALIVE_S = 15.0


class MatchRequest(BaseModel):
    seed: int = 42
    speed: float = Field(default=10, gt=0, le=10_000, description="playback speed; 1, 10 and 60 are typical")
    storyline: Storyline = "none"


class MatchInfo(BaseModel):
    match_id: str
    event_count: int
    seed: int
    sim_seed: int
    storyline: Storyline
    speed: float
    home: str
    away: str
    final_score: tuple[int, int]
    status: str = Field(description="ready | live | finished")


class Entry:
    def __init__(self, match: Match, speed: float):
        self.match = match
        self.speed = speed
        self.runtime: MatchRuntime | None = None

    def info(self) -> MatchInfo:
        rt = self.runtime
        status = "ready" if rt is None else "finished" if rt.done else "live"
        m = self.match
        return MatchInfo(
            match_id=m.match_id,
            event_count=len(m.events),
            seed=m.seed,
            sim_seed=m.sim_seed,
            storyline=m.storyline,
            speed=self.speed,
            home=m.home.name,
            away=m.away.name,
            final_score=m.final_score,
            status=status,
        )


MATCHES: dict[str, Entry] = {}


async def _prepare_demo_matches() -> None:
    """Generate seed 42 for every storyline up front, so the demo never waits on the simulator."""
    for storyline in get_args(Storyline):
        match_id = f"demo-{storyline}"
        if match_id in MATCHES:
            continue
        try:
            match = await run_in_threadpool(generate_match, DEMO_SEED, storyline, match_id)
        except Exception:  # a failed demo must not take the API down
            log.exception("could not prepare %s", match_id)
            continue
        MATCHES[match_id] = Entry(match, DEMO_SPEED)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    task = asyncio.create_task(_prepare_demo_matches())
    yield
    task.cancel()
    for entry in MATCHES.values():
        if entry.runtime:
            await entry.runtime.stop()


app = FastAPI(title="MatchGist", version=__version__, lifespan=lifespan)


def _entry(match_id: str) -> Entry:
    entry = MATCHES.get(match_id)
    if entry is None:
        raise HTTPException(404, f"no match {match_id!r}")
    return entry


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "version": __version__, "matches": len(MATCHES)}


@app.post("/matches", status_code=201)
async def create_match(req: MatchRequest) -> MatchInfo:
    match_id = f"m{sum(1 for k in MATCHES if not k.startswith('demo-')) + 1:03d}"
    # simulation is CPU-bound (1-10 s with a storyline): keep the event loop free
    match = await run_in_threadpool(generate_match, req.seed, req.storyline, match_id)
    MATCHES[match_id] = Entry(match, req.speed)
    return MATCHES[match_id].info()


@app.get("/matches")
async def list_matches() -> list[MatchInfo]:
    return [e.info() for e in MATCHES.values()]


@app.get("/matches/{match_id}/state")
async def match_state(match_id: str) -> dict[str, Any]:
    """Current Match State: live if the match is playing, otherwise pre-match (or final once finished)."""
    entry = _entry(match_id)
    state = entry.runtime.state if entry.runtime else MatchState(entry.match)
    return {
        "snapshot": state.snapshot(players=True),
        "moments": [m.model_dump() for m in state.moments],
        "momentum_series": state.momentum_series,
    }


def _sse(name: str, payload: Any) -> str:
    return f"event: {name}\ndata: {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}\n\n"


@app.get("/matches/{match_id}/stream")
async def stream(match_id: str, request: Request) -> StreamingResponse:
    """Server-Sent Events: ``snapshot`` first, then ``event``, ``stats`` and ``moment`` live, then ``end``.

    Playback starts with the first viewer and is shared by all viewers of the match.
    """
    entry = _entry(match_id)
    if entry.runtime is None:
        entry.runtime = MatchRuntime(entry.match, entry.speed)
    runtime = entry.runtime
    queue = runtime.subscribe()

    async def gen() -> AsyncIterator[str]:
        try:
            yield ": connected\n\n"
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=KEEPALIVE_S)
                except TimeoutError:
                    if await request.is_disconnected():
                        break
                    yield ": keepalive\n\n"
                    continue
                if item is None:
                    break
                yield _sse(*item)
        finally:
            runtime.unsubscribe(queue)

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)


@app.get("/fans")
async def list_fans() -> list[FanProfile]:
    return load_fans()
