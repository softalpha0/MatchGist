"""Supervisor and Verifier: the reliability layer around the language agents.

* Verifier: rejects any model output that cites a number not present in the
  facts (the main hallucination risk in sports graphics), is empty, or is too
  long for an on-screen cue.
* Supervisor: runs each agent call with a timeout, a per-session budget and a
  circuit breaker. Whatever goes wrong, it returns usable text by falling back
  to the deterministic template, and it records a trace so the recovery is
  visible in the Agent Ops panel.
"""

from __future__ import annotations

import asyncio
import re
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from touchline.agents.templates import numbers_allowed

NUMBER = re.compile(r"(?<![\w])\d+(?:[.,]\d+)?")
MAX_CHARS = 420
SCALES = {"10", "100"}  # rating denominators such as "7/10" or "62/100"


@dataclass
class Verdict:
    ok: bool
    reason: str = ""


def verify(text: str, facts: dict[str, Any]) -> Verdict:
    if not text or not text.strip():
        return Verdict(False, "empty output")
    if len(text) > MAX_CHARS:
        return Verdict(False, f"too long for a cue ({len(text)} chars)")
    allowed = numbers_allowed(facts) | SCALES
    for tok in NUMBER.findall(text):
        norm = tok.replace(",", ".")
        if "." in norm:
            norm = norm.rstrip("0").rstrip(".")
        if norm in allowed:
            continue
        # tolerate rounding of a real number, e.g. 0.23 -> 0.2 or 112.7 -> 113
        try:
            val = float(norm)
        except ValueError:
            return Verdict(False, f"unparseable number '{tok}'")
        if any(_close(val, a) for a in allowed):
            continue
        return Verdict(False, f"unsupported number '{tok}'")
    return Verdict(True)


def _close(val: float, allowed: str) -> bool:
    try:
        a = float(allowed)
    except ValueError:
        return False
    return abs(val - a) <= max(0.051, 0.006 * abs(a))


@dataclass
class Trace:
    agent: str
    insight_id: str
    status: str  # ok | fallback | rejected | timeout | error | skipped | breaker_open | repaired
    latency_ms: int
    model: str
    note: str = ""
    t: float = field(default_factory=time.time)

    def as_dict(self) -> dict:
        return {
            "agent": self.agent,
            "insight_id": self.insight_id,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "model": self.model,
            "note": self.note,
        }


@dataclass
class Supervisor:
    model_label: str
    timeout_s: float = 8.0
    budget: int = 120
    breaker_failures: int = 3
    breaker_cooldown_s: float = 30.0
    concurrency: int = 4
    calls: int = 0
    failures_in_row: int = 0
    breaker_open_until: float = 0.0
    traces: list[Trace] = field(default_factory=list)
    on_trace: Callable[[Trace], None] | None = None

    def __post_init__(self) -> None:
        self._sem = asyncio.Semaphore(self.concurrency)

    def _record(self, trace: Trace) -> Trace:
        self.traces.append(trace)
        if len(self.traces) > 500:
            del self.traces[:100]
        if self.on_trace:
            self.on_trace(trace)
        return trace

    def record(
        self, agent: str, insight_id: str, status: str, note: str = "", model: str = "deterministic"
    ) -> Trace:
        return self._record(Trace(agent, insight_id, status, 0, model, note))

    @property
    def breaker_open(self) -> bool:
        return time.monotonic() < self.breaker_open_until

    async def run(
        self,
        agent: str,
        insight_id: str,
        call: Callable[[], Awaitable[str]],
        fallback: Callable[[], str],
        facts: dict[str, Any],
    ) -> tuple[str, Trace]:
        """Run one agent call under supervision. Always returns text."""
        if self.breaker_open:
            return fallback(), self._record(
                Trace(agent, insight_id, "breaker_open", 0, self.model_label, "circuit open: using template")
            )
        if self.calls >= self.budget:
            return fallback(), self._record(
                Trace(agent, insight_id, "skipped", 0, self.model_label, "session model budget spent")
            )
        self.calls += 1
        start = time.perf_counter()
        status, note, text = "ok", "", ""
        try:
            async with self._sem:
                text = (await asyncio.wait_for(call(), timeout=self.timeout_s)).strip()
            verdict = verify(text, facts)
            if not verdict.ok:
                status, note = "rejected", verdict.reason
        except TimeoutError:
            status, note = "timeout", f"no answer in {self.timeout_s:.0f}s"
        except Exception as exc:  # noqa: BLE001 - any model/transport failure must degrade gracefully
            status, note = "error", f"{type(exc).__name__}: {str(exc)[:120]}"
        latency = int((time.perf_counter() - start) * 1000)
        if status == "ok":
            self.failures_in_row = 0
            return text, self._record(Trace(agent, insight_id, "ok", latency, self.model_label))
        if status in ("timeout", "error"):
            self.failures_in_row += 1
            if self.failures_in_row >= self.breaker_failures:
                self.breaker_open_until = time.monotonic() + self.breaker_cooldown_s
                note += f"; breaker opened for {self.breaker_cooldown_s:.0f}s"
                self.failures_in_row = 0
        return fallback(), self._record(
            Trace(agent, insight_id, status, latency, self.model_label, note + " → template fallback")
        )
