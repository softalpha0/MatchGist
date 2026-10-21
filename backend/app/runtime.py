"""Live playback: one shared runtime per match, fanned out to every viewer.

A runtime replays the match at its speed, folds each event into the Match State, detects moments and
publishes everything to subscriber queues. Moments go to the agent orchestrator through a queue, so a slow
model never stalls the match: deliveries and ``agent_event``s are published as they come out.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from app.agents.llm import LLMSettings
from app.agents.orchestrator import Orchestrator
from app.fans.profiles import FanProfile
from app.moments.detector import MatchAnalyzer
from app.moments.models import Moment
from app.simulator.engine import astream_events
from app.simulator.schema import Match
from app.state.match_state import MatchState

log = logging.getLogger(__name__)

STATS_EVERY_S = 15.0  # publish a stats snapshot every 15 s of match time (and after every moment)
QUEUE_MAX = 20_000
AGENT_EVENT_HISTORY = 400

Message = tuple[str, dict[str, Any]]  # (sse event name, payload)


@dataclass
class MatchRuntime:
    match: Match
    speed: float
    fans: list[FanProfile] = field(default_factory=list)
    settings: LLMSettings | None = None
    state: MatchState = field(init=False)
    subscribers: set[asyncio.Queue[Message | None]] = field(default_factory=set)
    task: asyncio.Task[None] | None = None
    done: bool = False

    def __post_init__(self) -> None:
        self.state = MatchState(self.match)
        self.analyzer = MatchAnalyzer(self.state)
        self._next_stats_t = 0.0
        self.agent_events: deque[dict[str, Any]] = deque(maxlen=AGENT_EVENT_HISTORY)
        self.orchestrator = Orchestrator(self.state, self.fans, self._on_agent_output, self.settings)
        self._work: asyncio.Queue[Moment | float | None] = asyncio.Queue()
        self._worker: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------ subscribers
    def subscribe(self) -> asyncio.Queue[Message | None]:
        """Join the live feed. Late joiners first get the state, moments, deliveries and recent decisions."""
        q: asyncio.Queue[Message | None] = asyncio.Queue(maxsize=QUEUE_MAX)
        q.put_nowait(("snapshot", self.snapshot_payload()))
        for m in self.state.moments:
            q.put_nowait(("moment", m.model_dump()))
        for s in self.orchestrator.sessions.values():
            for d in s.ledger.deliveries:
                q.put_nowait(("delivery", d.model_dump()))
        for e in self.agent_events:
            q.put_nowait(("agent_event", e))
        if self.done:
            q.put_nowait(("end", self.end_payload()))
            q.put_nowait(None)
            return q
        self.subscribers.add(q)
        if self.task is None:
            self._worker = asyncio.create_task(self._agents(), name=f"agents-{self.match.match_id}")
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

    def _on_agent_output(self, name: str, payload: dict[str, Any]) -> None:
        if name == "agent_event":
            self.agent_events.append(payload)
        self._publish(name, payload)

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            **self.state.snapshot(),
            "speed": self.speed,
            "storyline": self.match.storyline,
            "model": self.orchestrator.model_label,
            "fans": [s.fan.model_dump() for s in self.orchestrator.sessions.values()],
            "ledgers": {fid: s.ledger.summary() for fid, s in self.orchestrator.sessions.items()},
        }

    def end_payload(self) -> dict[str, Any]:
        return {
            "final_score": list(self.match.final_score),
            "ledgers": {fid: s.ledger.summary() for fid, s in self.orchestrator.sessions.items()},
        }

    # ------------------------------------------------------------------ fans
    def add_fan(self, fan: FanProfile) -> None:
        """A fan joining mid-match starts with a fresh budget from this moment on."""
        self.orchestrator.add_fan(fan)
        self._publish(
            "fan_joined",
            {
                "fan": fan.model_dump(),
                "match_clock": self.state.match_clock,
                "ledger": self.orchestrator.sessions[fan.fan_id].ledger.summary(),
            },
        )

    # ------------------------------------------------------------------ playback
    async def _run(self) -> None:
        try:
            last_minute = 0
            async for ev in astream_events(self.match, self.speed):
                moments = self.analyzer.feed(ev)
                self._publish("event", ev.model_dump(exclude_none=True))
                for m in moments:
                    self._publish("moment", m.model_dump())
                    self._work.put_nowait(m)
                if self.state.minute != last_minute and ev.type != "full_time":
                    last_minute = self.state.minute
                    self._work.put_nowait(float(last_minute))
                if moments or self.state.t >= self._next_stats_t or ev.type in ("half_time", "full_time"):
                    self._next_stats_t = self.state.t + STATS_EVERY_S
                    self._publish("stats", self.snapshot_payload())
            self._work.put_nowait(None)
            if self._worker:
                await self._worker  # let the full-time digests go out before "end"
        finally:
            self.done = True
            self._publish("stats", self.snapshot_payload())
            self._publish("end", self.end_payload())
            for q in list(self.subscribers):
                with contextlib.suppress(asyncio.QueueFull):
                    q.put_nowait(None)
            self.subscribers.clear()

    async def _agents(self) -> None:
        """Moments and minute ticks, in order, through the orchestrator."""
        while (item := await self._work.get()) is not None:
            try:
                if isinstance(item, Moment):
                    await self.orchestrator.on_moment(item)
                else:
                    await self.orchestrator.tick(item)
            except Exception:  # one bad moment must not stop the feed for everyone
                log.exception("orchestrator failed on %r", item)

    async def stop(self) -> None:
        for t in (self.task, self._worker):
            if t and not t.done():
                t.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await t
