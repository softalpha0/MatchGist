"""FastAPI app. M1: health, match creation and the demo fan personas. Streaming arrives in M2."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app import __version__
from app.fans.profiles import FanProfile, load_fans
from app.simulator.engine import generate_match
from app.simulator.schema import Match, Storyline

app = FastAPI(title="MatchGist", version=__version__)
MATCHES: dict[str, Match] = {}


class MatchRequest(BaseModel):
    seed: int = 42
    speed: float = Field(default=10, gt=0, le=600, description="playback speed for the stream (M2)")
    storyline: Storyline = "none"


class MatchCreated(BaseModel):
    match_id: str
    event_count: int
    seed: int
    sim_seed: int
    storyline: Storyline
    speed: float
    home: str
    away: str
    final_score: tuple[int, int]


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "version": __version__, "matches": len(MATCHES)}


@app.post("/matches", status_code=201)
async def create_match(req: MatchRequest) -> MatchCreated:
    match_id = f"m{len(MATCHES) + 1:03d}"
    # simulation is CPU-bound (1-6 s with a storyline): keep the event loop free
    match = await run_in_threadpool(generate_match, req.seed, req.storyline, match_id)
    MATCHES[match_id] = match
    return MatchCreated(
        match_id=match_id,
        event_count=len(match.events),
        seed=match.seed,
        sim_seed=match.sim_seed,
        storyline=match.storyline,
        speed=req.speed,
        home=match.home.name,
        away=match.away.name,
        final_score=match.final_score,
    )


@app.get("/fans")
async def list_fans() -> list[FanProfile]:
    return load_fans()
