"""One viewer session: a live synthetic match flowing through the agent pipeline to one screen."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import random
import time
from collections.abc import Awaitable, Callable
from typing import Any

from touchline.agents.pipeline import MatchPipeline
from touchline.agents.supervisor import Trace
from touchline.config import Settings
from touchline.models import Frame, MatchEvent, OverlayCue, Profile
from touchline.sim.engine import MatchEngine

log = logging.getLogger(__name__)

Send = Callable[[dict[str, Any]], Awaitable[None]]
TICK_WALL_S = 0.1
SPEEDS = (1, 2, 4, 8, 16, 32, 64)


class Session:
    def __init__(
        self,
        send: Send,
        settings: Settings,
        seed: int | None = None,
        profile: Profile | None = None,
        speed: float = 8,
        home: str | None = None,
        away: str | None = None,
    ):
        self.send = send
        self.settings = settings
        self.seed = seed if seed is not None else random.randint(1, 99999)
        self.engine = MatchEngine(self.seed, home, away)
        self.feed = self.engine.run()
        self.pending_traces: list[dict] = []
        self.pipeline = MatchPipeline(
            self.engine.meta, profile or Profile(), settings, on_trace=self._on_trace
        )
        self.speed = speed
        self.paused = False
        self.clock = 0.0
        self.done = False
        self.chaos_feed: list[str] = []
        self.tasks: set[asyncio.Task] = set()
        self.cues: dict[str, OverlayCue] = {}
        self.last_stats_wall = 0.0
        self._pending_frame: tuple[Frame, list[MatchEvent]] | None = None

    # ------------------------------------------------------------------ plumbing
    def _on_trace(self, trace: Trace) -> None:
        self.pending_traces.append(trace.as_dict())

    def _spawn(self, coro: Awaitable[Any]) -> None:
        task = asyncio.ensure_future(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def close(self) -> None:
        for t in list(self.tasks):
            t.cancel()
        self.done = True

    def hello(self) -> dict[str, Any]:
        meta = self.engine.meta
        return {
            "type": "hello",
            "seed": self.seed,
            "model": self.pipeline.model_label,
            "speed": self.speed,
            "speeds": SPEEDS,
            "profile": self.pipeline.profile.model_dump(mode="json"),
            "meta": meta.model_dump(mode="json"),
            "pitch": {"length": 105, "width": 68},
        }

    # ------------------------------------------------------------------ commands
    async def command(self, msg: dict[str, Any]) -> None:
        kind = msg.get("type")
        if kind == "profile":
            profile = Profile.model_validate(msg.get("profile", {}))
            self.pipeline.set_profile(profile)
            await self.send({"type": "profile", "profile": profile.model_dump(mode="json")})
            await self._replay_recent()
        elif kind == "speed":
            self.speed = float(msg.get("speed", self.speed))
        elif kind == "pause":
            self.paused = bool(msg.get("paused", not self.paused))
        elif kind == "chaos":
            await self._inject(str(msg.get("fault", "")))

    async def _replay_recent(self) -> None:
        """Profile flipped: re-render what is on screen and the feed for the new viewer."""
        recent = [i for i in self.pipeline.recent_insights(10) if i.kind not in ("sprint",)]
        for ins in recent[-6:]:
            cue = self.pipeline.director.cue_for(ins)
            if cue is None:
                continue
            cue.t_in = self.pipeline.state.t
            cue.t_out = cue.t_in + 8
            await self.send({"type": "cue", "cue": cue.model_dump(mode="json"), "replay": True})
            self._spawn(self._enrich(cue))

    async def _inject(self, fault: str) -> None:
        c = self.pipeline.chaos
        if fault == "model_outage":
            c.fail_next = 4
        elif fault == "hallucination":
            c.hallucinate_next = 2
        elif fault == "slow_model":
            c.slow_next = 1
            c.slow_seconds = self.settings.llm_timeout_s + 2
        elif fault in ("duplicate", "corrupt", "ghost", "reorder", "malformed"):
            self.chaos_feed.append(fault)
        else:
            return
        self.pipeline.supervisor.record("chaos", "-", "injected", f"fault injected: {fault}", "-")

    # ------------------------------------------------------------------ feed
    def _corrupt(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Apply queued feed faults to the raw wire events (demo of ingest recovery)."""
        if not self.chaos_feed or not raw:
            return raw
        fault = self.chaos_feed.pop(0)
        raw = [dict(e) for e in raw]
        if fault == "duplicate":
            raw.append(dict(raw[0]))
        elif fault == "corrupt":
            raw[0]["x"] = 160.0
            raw[0]["y"] = -12.0
        elif fault == "ghost":
            raw.append(
                {**raw[0], "id": raw[0]["id"] + "-ghost", "seq": raw[0]["seq"], "player_id": "ghost-99"}
            )
        elif fault == "reorder":
            raw.reverse()
            if len(raw) == 1:
                raw.append({**raw[0], "id": raw[0]["id"] + "-late", "seq": raw[0]["seq"] - 1})
        elif fault == "malformed":
            raw.append({"id": "garbage", "type": "teleport", "t": "soon"})
        return raw

    def _pull(self, until: float) -> tuple[list[Frame], list[dict[str, Any]]]:
        frames: list[Frame] = []
        raw: list[dict[str, Any]] = []
        while True:
            if self._pending_frame is None:
                try:
                    self._pending_frame = next(self.feed)
                except StopIteration:
                    self.done = True
                    break
            frame, events = self._pending_frame
            if frame.t > until:
                break
            self._pending_frame = None
            frames.append(frame)
            raw.extend(e.model_dump(mode="json") for e in events)
        return frames, raw

    # ------------------------------------------------------------------ main loop
    async def run(self) -> None:
        await self.send(self.hello())
        next_wall = time.monotonic()
        while not self.done:
            next_wall += TICK_WALL_S
            if not self.paused:
                self.clock += TICK_WALL_S * self.speed
                frames, raw = self._pull(self.clock)
                if frames:
                    raw = self._corrupt(raw)
                    out = await self.pipeline.tick(frames, raw)
                    await self._emit(out)
            await self._flush_traces()
            delay = next_wall - time.monotonic()
            if delay > 0:
                await asyncio.sleep(delay)
            else:
                next_wall = time.monotonic()
        # let in-flight enrichment (e.g. the full-time recap) finish
        if self.tasks:
            await asyncio.wait(list(self.tasks), timeout=self.settings.llm_timeout_s + 2)
        await self._flush_traces()
        await self.send({"type": "end", "stats": self.pipeline.state.snapshot()})

    async def _emit(self, out) -> None:  # type: ignore[no-untyped-def]
        if out.frame is not None:
            f = out.frame
            await self.send(
                {
                    "type": "frame",
                    "t": f.t,
                    "minute": f.minute,
                    "period": f.period,
                    "ball": f.ball,
                    "players": f.players,
                    "score": self.pipeline.state.score,
                    "possession": self.pipeline.state.possession,
                }
            )
        notable = [e for e in out.events if e.type.value not in ("pressure",)]
        if notable:
            await self.send(
                {
                    "type": "events",
                    "events": [e.model_dump(mode="json", exclude_none=True) for e in notable[-12:]],
                }
            )
        for cue in out.cues:
            self.cues[cue.id] = cue
            await self.send({"type": "cue", "cue": cue.model_dump(mode="json")})
            self._spawn(self._enrich(cue))
        now = time.monotonic()
        if now - self.last_stats_wall > 1.0:
            self.last_stats_wall = now
            await self.send(
                {
                    "type": "stats",
                    "stats": self.pipeline.state.snapshot(),
                    "players": self._player_table(),
                    "counters": self.pipeline.counters,
                }
            )

    def _player_table(self) -> dict[str, dict]:
        return {pid: ps.as_dict() for pid, ps in self.pipeline.state.players.items()}

    async def _enrich(self, cue: OverlayCue) -> None:
        ins = self.pipeline.insights.get(cue.insight_id)
        if ins is None:
            return
        try:
            update = await self.pipeline.enrich(ins)
        except Exception:  # never let one moment break the session
            log.exception("enrichment failed")
            return
        if update is None:
            return
        cue = cue.model_copy(update={"why": update.why, "revision": cue.revision + 1, "source": "agents"})
        self.cues[cue.id] = cue
        await self.send({"type": "cue", "cue": cue.model_dump(mode="json")})

    async def _flush_traces(self) -> None:
        if self.pending_traces:
            batch, self.pending_traces = self.pending_traces, []
            await self.send(
                {
                    "type": "traces",
                    "traces": batch[-50:],
                    "calls": self.pipeline.supervisor.calls,
                    "breaker_open": self.pipeline.supervisor.breaker_open,
                }
            )


async def run_session(session: Session) -> None:
    try:
        await session.run()
    finally:
        with contextlib.suppress(Exception):
            await session.close()
