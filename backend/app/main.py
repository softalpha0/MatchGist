"""FastAPI app: matches, the live SSE stream, fans and their ledgers, voice notes, and the web UI."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, get_args

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import __version__
from app.agents.llm import LLMSettings, make_clients
from app.config import REPO_ROOT
from app.fans.profiles import FanProfile, load_fans
from app.runtime import MatchRuntime
from app.simulator.engine import generate_match
from app.simulator.schema import Match, Storyline
from app.state.match_state import MatchState
from app.voice import tts

log = logging.getLogger(__name__)

DEMO_SEED = 42
DEMO_SPEED = 60.0
KEEPALIVE_S = 15.0
MAX_FANS_PER_MATCH = 16
MAX_LIVE_MATCHES = 40
FRONTEND_DIR = Path(os.getenv("FRONTEND_DIST", REPO_ROOT / "frontend" / "out"))


class MatchRequest(BaseModel):
    seed: int = 42
    speed: float = Field(default=10, gt=0, le=10_000, description="playback speed; 1, 10 and 60 are typical")
    storyline: Storyline = "none"


class ReplayRequest(BaseModel):
    speed: float | None = Field(default=None, gt=0, le=10_000)


class MatchInfo(BaseModel):
    match_id: str
    source_id: str
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
    def __init__(self, match_id: str, match: Match, speed: float):
        self.match_id = match_id
        self.match = match
        self.speed = speed
        self.runtime: MatchRuntime | None = None

    def info(self) -> MatchInfo:
        rt = self.runtime
        status = "ready" if rt is None else "finished" if rt.done else "live"
        m = self.match
        return MatchInfo(
            match_id=self.match_id,
            source_id=m.match_id,
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

    def ensure_runtime(self) -> MatchRuntime:
        if self.runtime is None:
            self.runtime = MatchRuntime(self.match, self.speed, fans=load_fans(), settings=SETTINGS)
        return self.runtime


MATCHES: dict[str, Entry] = {}
SETTINGS = LLMSettings.from_env()


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
        MATCHES[match_id] = Entry(match_id, match, DEMO_SPEED)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    task = asyncio.create_task(_prepare_demo_matches())
    yield
    task.cancel()
    for entry in MATCHES.values():
        if entry.runtime:
            await entry.runtime.stop()


app = FastAPI(title="MatchGist", version=__version__, lifespan=lifespan, docs_url="/api/docs", redoc_url=None)
# the Next.js dev server runs on another port; in production the UI is served from this app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _entry(match_id: str) -> Entry:
    entry = MATCHES.get(match_id)
    if entry is None:
        raise HTTPException(404, f"no match {match_id!r}")
    return entry


def _live_count() -> int:
    return sum(1 for e in MATCHES.values() if e.runtime and not e.runtime.done)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "version": __version__, "matches": len(MATCHES), "live": _live_count()}


@app.get("/config")
async def config() -> dict[str, Any]:
    """What the UI should say about the backends in use."""
    label = make_clients(SETTINGS)[2] if SETTINGS.mode != "offline" else "offline-templates"
    return {
        "model": label,
        "llm_mode": SETTINGS.mode,
        "speech": tts.configured(),
        "storylines": list(get_args(Storyline)),
        "demo_seed": DEMO_SEED,
    }


@app.post("/matches", status_code=201)
async def create_match(req: MatchRequest) -> MatchInfo:
    match_id = f"m{sum(1 for k in MATCHES if not k.startswith('demo-')) + 1:03d}"
    # simulation is CPU-bound (1-10 s with a storyline): keep the event loop free
    match = await run_in_threadpool(generate_match, req.seed, req.storyline, match_id)
    MATCHES[match_id] = Entry(match_id, match, req.speed)
    return MATCHES[match_id].info()


@app.post("/matches/{match_id}/replay", status_code=201)
async def replay(match_id: str, req: ReplayRequest | None = None) -> MatchInfo:
    """A fresh live run of an existing match (instant: no re-simulation). Each viewer can get their own."""
    if _live_count() >= MAX_LIVE_MATCHES:
        raise HTTPException(429, "too many live matches right now; try again in a minute")
    src = _entry(match_id)
    n = sum(1 for k in MATCHES if k.startswith(f"{src.match.match_id}-r")) + 1
    new_id = f"{src.match.match_id}-r{n}"
    MATCHES[new_id] = Entry(new_id, src.match, (req.speed if req and req.speed else src.speed))
    return MATCHES[new_id].info()


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
    """Server-Sent Events: ``snapshot`` first, then ``event``, ``stats``, ``moment``, ``delivery`` and
    ``agent_event`` live, then ``end``. Playback starts with the first viewer and is shared by all viewers.
    """
    runtime = _entry(match_id).ensure_runtime()
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


def _session(match_id: str, fan_id: str):  # type: ignore[no-untyped-def]
    rt = _entry(match_id).runtime
    if rt is None or fan_id not in rt.orchestrator.sessions:
        raise HTTPException(404, f"fan {fan_id!r} has nothing for match {match_id!r} yet")
    return rt.orchestrator.sessions[fan_id]


@app.get("/matches/{match_id}/fans/{fan_id}/ledger")
async def ledger(match_id: str, fan_id: str) -> dict[str, Any]:
    """Everything sent to a fan, data used, pings left, and which limit binds."""
    s = _session(match_id, fan_id)
    return {**s.ledger.summary(), "deliveries": [d.model_dump() for d in s.ledger.deliveries]}


@app.get("/matches/{match_id}/fans/{fan_id}/digest")
async def fan_digest(match_id: str, fan_id: str) -> dict[str, Any]:
    s = _session(match_id, fan_id)
    digests = [d for d in s.ledger.deliveries if d.kind == "digest"]
    if not digests:
        raise HTTPException(404, "no digest yet (it is sent at full time)")
    return digests[-1].model_dump()


@app.post("/matches/{match_id}/fans", status_code=201)
async def add_fan_to_match(match_id: str, fan: FanProfile) -> dict[str, Any]:
    """Add a fan to a match; if it is live, they join from the current minute with a fresh budget."""
    rt = _entry(match_id).ensure_runtime()
    if fan.fan_id in rt.orchestrator.sessions:
        raise HTTPException(409, f"fan {fan.fan_id!r} is already in this match")
    if len(rt.orchestrator.sessions) >= MAX_FANS_PER_MATCH:
        raise HTTPException(429, f"at most {MAX_FANS_PER_MATCH} fans per match")
    rt.add_fan(fan)
    return rt.orchestrator.sessions[fan.fan_id].ledger.summary()


@app.get("/fans")
async def list_fans() -> list[FanProfile]:
    return load_fans()


@app.get("/audio/{delivery_id}.ogg")
async def audio(delivery_id: str) -> Response:
    data = tts.AUDIO_STORE.get(delivery_id)
    if data is None:
        raise HTTPException(404, "no audio for this delivery")
    return Response(data, media_type="audio/ogg")


# ---------------------------------------------------------------------- web UI (static Next.js export)
NOT_BUILT = """<!doctype html><meta charset="utf-8"><title>MatchGist</title>
<body style="font-family:system-ui;background:#0b0f14;color:#e6edf5;max-width:640px;margin:10vh auto">
<h1>MatchGist API is running</h1>
<p>The website hasn't been built yet (no <code>frontend/out</code> folder). In PowerShell:</p>
<pre style="background:#121821;padding:12px;border-radius:8px">cd frontend
npm install
npm run build</pre>
<p>Then restart <code>uvicorn</code> and reload this page. The API docs are at <a style="color:#b8f35a"
href="/api/docs">/api/docs</a>.</p></body>"""

if not FRONTEND_DIR.is_dir():

    @app.get("/", include_in_schema=False)
    @app.get("/live", include_in_schema=False)
    async def not_built() -> Response:
        return Response(NOT_BUILT, media_type="text/html")

else:

    @app.get("/live")
    async def live_page() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "live.html")

    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="web")
