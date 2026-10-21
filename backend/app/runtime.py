"""Live playback: one shared runtime per match, fanned out to every viewer.

A runtime replays the match at its speed, folds each event into the Match State, detects moments and
publishes everything to subscriber queues. Running it once per match (not once per viewer) is what lets
M3 compute each fan's deliveries a single time and show them to everyone watching.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from dataclasses import dataclass, field
from typing import Any

from app.moments.detector import MatchAnalyzer
from app.simulator.engine import astream_events
from app.simulator.schema import Match
from app.state.match_state import MatchState

log = logging.getLogger(__name__)

STATS_EVERY_S = 15.0  # publish a stats snapshot every 15 s of match time (and after every moment)
QUEUE_MAX = 10_000

Message = tuple[str, dict[str, Any]]  # (sse event name, payload)


@dataclass
class MatchRuntime:
    match: Match
    speed: float
    state: MatchState = field(init=False)
    subscribers: set[asyncio.Queue[Message | None]] = field(default_factory=set)
    task: asyncio.Task[None] | None = None
    done: bool = False

    def __post_init__(self) -> None:
        self.state = MatchState(self.match)
        self.analyzer = MatchAnalyzer(self.state)
        self._next_stats_t = 0.0

    # ------------------------------------------------------------------ subscribers
    def subscribe(self) -> asyncio.Queue[Message | None]:
        """Join the live feed. Late joiners first get the current state and the moments so far."""
        q: asyncio.Queue[Message | None] = asyncio.Queue(maxsize=QUEUE_MAX)
        q.put_nowait(("snapshot", self.snapshot_payload()))
        for m in self.state.moments:
            q.put_nowait(("moment", m.model_dump()))
        if self.done:
            q.put_nowait(("end", {"final_score": list(self.match.final_score)}))
            q.put_nowait(None)
            return q
        self.subscribers.add(q)
        if self.task is None:
            self.task = asyncio.create_task(self._run(), name=f"runtime-{self.match.match_id}")
        return q

    def unsubscribe(self, q: asyncio.Queue[Message | None]) -> None:
        self.subscribers.discard(q)

    def _publish(self, name: str, payload: dict[str, Any]) -> None:
        for q in list(self.subscribers):
            try:
                q.put_nowait((name, payload))
            except asyncio.QueueFull:
                # a viewer that can't keep up is dropped rather than allowed to stall the match
                log.warning("dropping slow subscriber on %s", self.match.match_id)
                self.subscribers.discard(q)
                with contextlib.suppress(asyncio.QueueFull):
                    q.put_nowait(None)

    def snapshot_payload(self) -> dict[str, Any]:
        return {**self.state.snapshot(), "speed": self.speed, "storyline": self.match.storyline}

    # ------------------------------------------------------------------ playback
    async def _run(self) -> None:
        try:
            async for ev in astream_events(self.match, self.speed):
                moments = self.analyzer.feed(ev)
                self._publish("event", ev.model_dump(exclude_none=True))
                for m in moments:
                    self._publish("moment", m.model_dump())
                if moments or self.state.t >= self._next_stats_t or ev.type in ("half_time", "full_time"):
                    self._next_stats_t = self.state.t + STATS_EVERY_S
                    self._publish("stats", self.snapshot_payload())
        finally:
            self.done = True
            self._publish("end", {"final_score": list(self.match.final_score)})
            for q in list(self.subscribers):
                with contextlib.suppress(asyncio.QueueFull):
                    q.put_nowait(None)
            self.subscribers.clear()

    async def stop(self) -> None:
        if self.task and not self.task.done():
            self.task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.task
