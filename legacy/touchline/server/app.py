"""HTTP + WebSocket front door. Serves the web client and one live session per socket."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from touchline import __version__
from touchline.config import get_settings
from touchline.models import OverlayCue, Profile
from touchline.server.session import Session, run_session
from touchline.sim.clubs import CLUBS

log = logging.getLogger(__name__)
WEB_DIR = Path(__file__).resolve().parents[2] / "web"
DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"

settings = get_settings()
app = FastAPI(
    title="Touchline",
    version=__version__,
    description="Multi-agent synthetic match intelligence",
    docs_url="/api/docs",
    redoc_url=None,
)
MODEL_LABEL = f"foundry:{settings.foundry_model}" if settings.use_foundry else "touchline-offline-templates"
_active: set[Session] = set()


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "version": __version__, "model": MODEL_LABEL, "sessions": len(_active)}


@app.get("/api/clubs")
async def clubs() -> list[dict[str, Any]]:
    return [c.model_dump(mode="json") for c in CLUBS]


@app.get("/api/schema/cue")
async def cue_schema() -> JSONResponse:
    """JSON Schema of the overlay cue a broadcast graphics engine consumes."""
    return JSONResponse(OverlayCue.model_json_schema())


@app.get("/api/schema/profile")
async def profile_schema() -> JSONResponse:
    return JSONResponse(Profile.model_json_schema())


@app.websocket("/ws/match")
async def match_socket(ws: WebSocket) -> None:
    await ws.accept()
    if len(_active) >= settings.max_sessions:
        await ws.send_json({"type": "error", "message": "Server is at capacity, please retry in a minute."})
        await ws.close()
        return
    q = ws.query_params
    try:
        seed = int(q["seed"]) if q.get("seed") else None
        speed = float(q.get("speed", 8))
        profile = Profile.model_validate(json.loads(q["profile"])) if q.get("profile") else Profile()
    except (ValueError, KeyError) as exc:
        await ws.send_json({"type": "error", "message": f"bad parameters: {exc}"})
        await ws.close()
        return
    home, away = q.get("home"), q.get("away")
    valid = {c.id for c in CLUBS}
    if home not in valid or away not in valid or home == away:
        home = away = None

    send_lock = asyncio.Lock()

    async def send(msg: dict[str, Any]) -> None:
        async with send_lock:
            await ws.send_text(json.dumps(msg, separators=(",", ":"), default=str))

    session = Session(send, settings, seed=seed, profile=profile, speed=speed, home=home, away=away)
    _active.add(session)
    runner = asyncio.create_task(run_session(session))
    try:
        while not runner.done():
            recv = asyncio.create_task(ws.receive_text())
            done, _ = await asyncio.wait({recv, runner}, return_when=asyncio.FIRST_COMPLETED)
            if recv in done:
                try:
                    await session.command(json.loads(recv.result()))
                except (ValueError, TypeError) as exc:
                    await send({"type": "error", "message": str(exc)[:200]})
            else:
                recv.cancel()
        # keep the socket open after full time so the viewer can read the recap
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001
        log.exception("session crashed")
    finally:
        runner.cancel()
        with contextlib.suppress(BaseException):
            await runner
        await session.close()
        _active.discard(session)


@app.get("/docs/{name}")
async def docs(name: str) -> FileResponse:
    path = (DOCS_DIR / name).resolve()
    if path.parent != DOCS_DIR or not path.is_file():
        raise HTTPException(404)
    return FileResponse(path)


app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
