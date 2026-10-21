"""Orchestrator: Explainer once per moment, then one Agent Framework workflow per fan, run in parallel.

Per-fan workflow (Microsoft Agent Framework ``WorkflowBuilder``)::

    Dispatcher ─ moment ─► Ranker ─► BudgetGuard ─ send ─► Localizer ─► Compressor ─► Verifier ─ ok ─► Deliver
        │                               │ hold/skip ────────────────────────────────────────────────►│
        └─ bundle / digest ─────────────────────────────► Localizer          ▲     │ reject (≤2 retries)
                                                                             └─────┘

Shared state: the Match State (read-only here) and each fan's ledger and held bundle. Every step emits an
``agent_event`` (decisions with reasons, rejections, fallbacks), so the System panel shows the whole chain.
Recovery: a Verifier rejection goes back to the Compressor with the exact reason, up to twice. After that,
or on any model failure, a per-channel, per-language template takes over, so the feed never stops.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from agent_framework import Executor, WorkflowBuilder, WorkflowContext, handler

from app.agents import compressor, digest, explainer, localizer
from app.agents.budget_guard import BUNDLE_WINDOW_MIN, Decision, decide
from app.agents.fallbacks import LATIN, T, compose, fit_text, render, strip_accents
from app.agents.llm import AgentResult, LLMSettings, call_agent, make_clients, shared_cap
from app.agents.ranker import Ranking, rank
from app.agents.verifier import Verdict, verify
from app.channels.adapters import overlay_cue
from app.channels.limits import Message, estimate_voice_seconds
from app.channels.sizing import size_kb
from app.channels.sms_encoding import analyze_sms
from app.fans.profiles import FanProfile
from app.moments.models import Moment
from app.state.ledger import Delivery, Ledger
from app.state.match_state import MatchState
from app.voice import tts

MAX_COMPRESS_ATTEMPTS = 3  # first try + 2 retries after Verifier rejections

Emit = Callable[[str, dict[str, Any]], None]


@dataclass
class FanSession:
    fan: FanProfile
    ledger: Ledger
    held: list[Moment] = field(default_factory=list)


@dataclass
class FanJob:
    session: FanSession
    moments: list[Moment]
    kind: Literal["moment", "bundle", "digest"]
    explanations: dict[str, str]
    ranking: Ranking | None = None
    decision: Decision | None = None
    text: str = ""
    message: Message | None = None
    verdict: Verdict | None = None
    attempts: int = 0
    feedback: str | None = None
    fallback_used: bool = False
    max_segments: int = 1
    reason: str = ""
    delivery: Delivery | None = None

    @property
    def fan(self) -> FanProfile:
        return self.session.fan

    @property
    def lead(self) -> Moment:
        return self.moments[0]

    @property
    def needs_retry(self) -> bool:
        return self.verdict is not None and not self.verdict.ok and self.attempts < MAX_COMPRESS_ATTEMPTS


@dataclass(frozen=True)
class Verified:
    """Verifier output. Immutable, so workflow edge conditions can't see later mutations of the job."""

    job: FanJob
    retry: bool


class Orchestrator:
    def __init__(
        self,
        state: MatchState,
        fans: list[FanProfile],
        emit: Emit,
        settings: LLMSettings | None = None,
        clients: tuple[Any, Any, str] | None = None,
    ):
        self.state = state
        self.emit = emit
        self.settings = settings or LLMSettings.from_env()
        fast, slow, self.model_label = clients or make_clients(self.settings)
        self.cap = shared_cap(self.settings)
        self.agents = {
            "explainer": explainer.build(fast),
            "localizer": localizer.build(fast),
            "compressor": compressor.build(fast),
            "digest": digest.build(slow),
        }
        self.sessions: dict[str, FanSession] = {}
        for fan in fans:
            self.add_fan(fan)
        self.explanations: dict[str, str] = {}
        self._n_delivery = 0
        self._n_cue = 0
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------ fans
    def add_fan(self, fan: FanProfile) -> FanSession:
        session = FanSession(fan, Ledger.for_fan(fan))
        self.sessions[fan.fan_id] = session
        return session

    async def call(self, agent: str, message: str):  # type: ignore[no-untyped-def]
        st = self.settings
        refused = self.cap.take()
        if refused:  # a failed result, so the caller's usual template fallback (and its log line) runs
            return AgentResult("", False, 0, 0, refused)
        return await call_agent(
            self.agents[agent], message, timeout_s=st.timeout_s, retries=st.retries, backoff_s=st.backoff_s
        )

    # ------------------------------------------------------------------ events
    def event(
        self,
        agent: str,
        action: str,
        detail: str,
        *,
        fan: FanProfile | None = None,
        moment: Moment | None = None,
        latency_ms: int | None = None,
    ) -> None:
        self.emit(
            "agent_event",
            {
                "ts": round(time.time(), 3),
                "match_clock": (moment.match_clock if moment else self.state.match_clock),
                "agent": agent,
                "action": action,
                "detail": detail,
                "fan_id": fan.fan_id if fan else None,
                "moment_id": moment.moment_id if moment else None,
                "latency_ms": latency_ms,
                "model": self.model_label
                if agent in ("explainer", "localizer", "compressor", "digest")
                else None,
            },
        )

    # ------------------------------------------------------------------ entry points
    async def on_moment(self, moment: Moment) -> None:
        """Explain once, then run every fan's chain in parallel."""
        async with self._lock:
            await self._explain(moment)
            if moment.type == "full_time":
                jobs = [self._digest_job(s, moment) for s in self.sessions.values()]
            else:
                jobs = [FanJob(s, [moment], "moment", self.explanations) for s in self.sessions.values()]
            await asyncio.gather(*(self._run(j) for j in jobs if j is not None))

    async def tick(self, minute: float) -> None:
        """Flush held bundles older than the bundle window."""
        async with self._lock:
            jobs = []
            for s in self.sessions.values():
                if s.held and minute - s.held[0].minute >= BUNDLE_WINDOW_MIN:
                    held, s.held = s.held, []
                    jobs.append(
                        FanJob(
                            s,
                            held,
                            "bundle" if len(held) > 1 else "moment",
                            self.explanations,
                            reason=f"bundle of {len(held)} after {BUNDLE_WINDOW_MIN:.0f} min"
                            if len(held) > 1
                            else "held moment released",
                        )
                    )
            await asyncio.gather(*(self._run(j, start_at_localizer=True) for j in jobs))

    def _digest_job(self, s: FanSession, ft: Moment) -> FanJob | None:
        s.held.clear()
        if s.fan.channel == "broadcast":
            return FanJob(s, [ft], "moment", self.explanations)
        led = s.ledger
        if (led.pings_left is not None and led.pings_left <= 0) or (
            led.data_left_kb is not None and led.data_left_kb < 0.2
        ):
            self.event(
                "budget_guard", "skip", "full time, but no budget left for a digest", fan=s.fan, moment=ft
            )
            return None
        return FanJob(
            s, [ft], "digest", self.explanations, reason="full time: digest sized to remaining budget"
        )

    async def _explain(self, moment: Moment) -> None:
        if moment.moment_id in self.explanations:
            return
        res = await self.call("explainer", explainer.request(moment))
        text = res.text if res.ok else explainer.fallback(moment)
        if res.ok and verify(Message(channel="broadcast", text=text), moment.facts).ok:
            self.event("explainer", "explained", text, moment=moment, latency_ms=res.latency_ms)
        else:
            text = explainer.fallback(moment)
            why = res.error or "explanation cited unsupported numbers"
            self.event(
                "explainer", "fallback", f"{why}: template used", moment=moment, latency_ms=res.latency_ms
            )
        self.explanations[moment.moment_id] = text

    async def _run(self, job: FanJob, start_at_localizer: bool = False) -> None:
        if start_at_localizer:
            job.decision = Decision("send", job.reason or "released", max_segments=1)
        await build_workflow(self).run(job)


# --------------------------------------------------------------------------- executors
class Dispatcher(Executor):
    def __init__(self) -> None:
        super().__init__(id="dispatcher")

    @handler
    async def dispatch(self, job: FanJob, ctx: WorkflowContext[FanJob]) -> None:
        await ctx.send_message(job)


class RankerExec(Executor):
    def __init__(self, orch: Orchestrator):
        super().__init__(id="ranker")
        self.o = orch

    @handler
    async def run(self, job: FanJob, ctx: WorkflowContext[FanJob]) -> None:
        job.ranking = rank(job.fan, job.lead)
        self.o.event(
            "ranker",
            "scored",
            f"{job.ranking.score}: " + ", ".join(job.ranking.reasons),
            fan=job.fan,
            moment=job.lead,
        )
        await ctx.send_message(job)


class GuardExec(Executor):
    def __init__(self, orch: Orchestrator):
        super().__init__(id="budget_guard")
        self.o = orch

    @handler
    async def run(self, job: FanJob, ctx: WorkflowContext[FanJob]) -> None:
        assert job.ranking
        s = job.session
        d = decide(job.fan, s.ledger, job.lead, job.ranking)
        job.decision, job.reason, job.max_segments = d, d.reason, d.max_segments
        if d.action == "hold":
            s.held.append(job.lead)
            s.ledger.held += 1
        elif d.action == "skip":
            s.ledger.skipped += 1
        elif s.held:  # a strong moment carries anything waiting with it, in one ping
            job.moments = [job.lead, *s.held]
            s.held = []
            job.kind = "bundle"
            job.reason += f" (+{len(job.moments) - 1} held, bundled)"
        self.o.event("budget_guard", d.action, job.reason, fan=job.fan, moment=job.lead)
        await ctx.send_message(job)


class LocalizerExec(Executor):
    def __init__(self, orch: Orchestrator):
        super().__init__(id="localizer")
        self.o = orch

    @handler
    async def run(self, job: FanJob, ctx: WorkflowContext[FanJob]) -> None:
        fan, o = job.fan, self.o
        if job.kind == "digest":
            budget = digest.budget_for(fan, job.session.ledger)
            res = await o.call("digest", digest.request(job.lead, fan, budget, localizer.depth(fan)))
            job.text = (
                res.text
                if res.ok
                else digest.template(job.lead, fan.language, fan.channel, localizer.depth(fan))
            )
            job.fallback_used |= not res.ok
            job.max_segments = budget.get("max_segments", 1)
            o.event(
                "digest",
                "written" if res.ok else "fallback",
                f"budget {budget}: {job.text[:120]}",
                fan=fan,
                moment=job.lead,
                latency_ms=res.latency_ms,
            )
        else:
            parts = [await self._localize(job, m) for m in job.moments[:1]]
            more = [render(m.type, m.facts, fan.language, "short") for m in job.moments[1:]]
            if more:
                parts.append(T.get(fan.language, T["en"])["_more"]["bundle"] + " " + "; ".join(more))
            job.text = " ".join(parts)
        await ctx.send_message(job)

    async def _localize(self, job: FanJob, m: Moment) -> str:
        fan, o = job.fan, self.o
        explanation = job.explanations.get(m.moment_id) or explainer.fallback(m)
        if fan.language == "en" and localizer.depth(fan) == "analyst":
            o.event("localizer", "skipped", "explanation already fits (English, analyst)", fan=fan, moment=m)
            return explanation
        res = await o.call("localizer", localizer.request(m, fan, explanation))
        if res.ok:
            o.event(
                "localizer",
                "localized",
                f"{fan.language}: {res.text[:120]}",
                fan=fan,
                moment=m,
                latency_ms=res.latency_ms,
            )
            return res.text
        job.fallback_used = True
        o.event("localizer", "fallback", f"{res.error}: {fan.language} template", fan=fan, moment=m)
        return localizer.fallback(m, fan)


class CompressorExec(Executor):
    def __init__(self, orch: Orchestrator):
        super().__init__(id="compressor")
        self.o = orch

    @handler
    async def first(self, job: FanJob, ctx: WorkflowContext[FanJob]) -> None:
        await self.run(job, ctx)

    @handler
    async def again(self, v: Verified, ctx: WorkflowContext[FanJob]) -> None:
        await self.run(v.job, ctx)

    async def run(self, job: FanJob, ctx: WorkflowContext[FanJob]) -> None:
        fan, o = job.fan, self.o
        job.attempts += 1
        facts = merged_facts(job.moments)
        req = compressor.request(
            text=job.text,
            mtype=job.lead.type,
            facts=facts,
            language=fan.language,
            channel=fan.channel,
            depth=localizer.depth(fan),
            max_segments=job.max_segments,
            attempt=job.attempts,
            feedback=job.feedback,
        )
        res = await o.call("compressor", req)
        msg = compressor.to_message(res.text, fan.channel, fan.language) if res.ok else None
        if msg is None:
            job.fallback_used = True
            msg = compose(
                job.lead.type,
                job.lead.facts,
                fan.language,
                fan.channel,
                localizer.depth(fan),
                job.max_segments,
            )
            o.event(
                "compressor",
                "fallback",
                f"{res.error or 'unparseable reply'}: template fitted",
                fan=fan,
                moment=job.lead,
                latency_ms=res.latency_ms,
            )
        else:
            o.event(
                "compressor",
                f"attempt {job.attempts}",
                describe(msg),
                fan=fan,
                moment=job.lead,
                latency_ms=res.latency_ms,
            )
        if fan.channel == "sms" and fan.language in LATIN:
            stripped = strip_accents(msg.text)
            if analyze_sms(stripped).segments < analyze_sms(msg.text).segments:
                o.event(
                    "compressor",
                    "gsm7",
                    "accents dropped to stay GSM-7 (saves a segment)",
                    fan=fan,
                    moment=job.lead,
                )
                msg = Message(channel="sms", text=stripped, language=fan.language)
        job.message = msg
        await ctx.send_message(job)


class VerifierExec(Executor):
    def __init__(self, orch: Orchestrator):
        super().__init__(id="verifier")
        self.o = orch

    @handler
    async def run(self, job: FanJob, ctx: WorkflowContext[Verified]) -> None:
        assert job.message
        o, fan = self.o, job.fan
        facts = merged_facts(job.moments)
        # deliveries may cite only the moment's facts: the full snapshot is too number-rich to prove much
        snap = None
        job.verdict = verify(job.message, facts, snap, job.max_segments)
        if job.verdict.ok:
            o.event("verifier", "pass", describe(job.message), fan=fan, moment=job.lead)
        elif job.needs_retry:
            job.feedback = "; ".join(job.verdict.reasons)
            o.event("verifier", "reject", job.feedback + " → back to Compressor", fan=fan, moment=job.lead)
        else:
            reasons = "; ".join(job.verdict.reasons)
            job.message = safe_fallback(job, snap)
            job.verdict = verify(job.message, facts, snap, job.max_segments)
            job.fallback_used = True
            o.event(
                "verifier",
                "fallback",
                f"{reasons} after {job.attempts} attempts → template",
                fan=fan,
                moment=job.lead,
            )
        await ctx.send_message(Verified(job, retry=not job.verdict.ok and job.needs_retry))


class DeliverExec(Executor):
    def __init__(self, orch: Orchestrator):
        super().__init__(id="deliver")
        self.o = orch

    @handler
    async def from_guard(self, job: FanJob, ctx: WorkflowContext[None, FanJob]) -> None:
        await self.run(job, ctx)

    @handler
    async def from_verifier(self, v: Verified, ctx: WorkflowContext[None, FanJob]) -> None:
        await self.run(v.job, ctx)

    async def run(self, job: FanJob, ctx: WorkflowContext[None, FanJob]) -> None:
        if job.decision is not None and job.decision.action != "send" and job.kind != "digest":
            await ctx.yield_output(job)
            return
        assert job.message
        o, fan, msg = self.o, job.fan, job.message
        o._n_delivery += 1
        did = f"d-{o._n_delivery:04d}"
        kb = size_kb(msg)
        audio_url = voice = None
        seconds = None
        if fan.channel == "voice":
            note = await tts.synthesize(msg.text, fan.language)
            voice = note.voice
            if note.audio is not None:
                tts.AUDIO_STORE[did] = note.audio
                audio_url = f"/audio/{did}.ogg"
                seconds, kb = note.seconds, note.size_kb or kb
            else:
                seconds = estimate_voice_seconds(msg.text, fan.language)
                job.fallback_used = job.fallback_used or tts.configured()
            o.event(
                "voice",
                "synthesised" if audio_url else "text",
                f"{note.note}; {seconds}s, {kb} KB",
                fan=fan,
                moment=job.lead,
            )
        overlay = None
        kind: Any = job.kind
        if fan.channel == "broadcast":
            o._n_cue += 1
            overlay = overlay_cue(job.lead, msg.text, o._n_cue)
            kind = "overlay"
        info = analyze_sms(msg.text) if fan.channel == "sms" else None
        delivery = Delivery(
            delivery_id=did,
            fan_id=fan.fan_id,
            kind=kind,
            moment_ids=[m.moment_id for m in job.moments],
            channel=fan.channel,
            language=fan.language,
            match_clock=job.lead.match_clock,
            text=msg.text,
            title=msg.title,
            value=msg.value,
            audio_url=audio_url,
            audio_seconds=seconds,
            voice=voice,
            size_kb=kb,
            segments=info.segments if info else None,
            encoding=info.encoding if info else None,
            decision_reason=job.reason,
            fallback_used=job.fallback_used,
            attempts=job.attempts,
            overlay=overlay,
        )
        job.delivery = job.session.ledger.record(delivery)
        o.emit("delivery", job.delivery.model_dump())
        await ctx.yield_output(job)


def build_workflow(orch: Orchestrator):  # type: ignore[no-untyped-def]
    dispatcher = Dispatcher()
    ranker, guard = RankerExec(orch), GuardExec(orch)
    loc, comp, ver, deliver = LocalizerExec(orch), CompressorExec(orch), VerifierExec(orch), DeliverExec(orch)
    return (
        WorkflowBuilder(name="matchgist-fan-chain", start_executor=dispatcher, max_iterations=40)
        .add_edge(dispatcher, ranker, condition=lambda j: j.decision is None and j.kind == "moment")
        .add_edge(dispatcher, loc, condition=lambda j: j.decision is not None or j.kind == "digest")
        .add_edge(ranker, guard)
        .add_edge(guard, loc, condition=lambda j: j.decision.action == "send")
        .add_edge(guard, deliver, condition=lambda j: j.decision.action != "send")
        .add_edge(loc, comp)
        .add_edge(comp, ver)
        .add_edge(ver, comp, condition=lambda v: v.retry)
        .add_edge(ver, deliver, condition=lambda v: not v.retry)
        .build()
    )


# --------------------------------------------------------------------------- helpers
def merged_facts(moments: list[Moment]) -> dict[str, Any]:
    """All facts the delivery may cite (a bundle may cite any of its moments)."""
    if len(moments) == 1:
        return moments[0].facts
    return {m.moment_id: m.facts for m in moments}


def describe(msg: Message) -> str:
    if msg.channel == "sms":
        info = analyze_sms(msg.text)
        return f"{info.segments} seg, {info.units} {info.encoding} units: {msg.text[:90]}"
    if msg.channel == "push":
        return f"title {len(msg.title or '')}c, body {len(msg.text)}c: {msg.title}"
    if msg.channel == "watch":
        return f"{len(msg.text)}c + value {msg.value}: {msg.text}"
    return f"{len(msg.text)}c: {msg.text[:90]}"


def safe_fallback(job: FanJob, snap: dict[str, Any]) -> Message:
    """Template that is guaranteed to pass: compose, then trim words if a bundle or digest still overflows."""
    fan = job.fan
    msg = compose(
        job.lead.type, job.lead.facts, fan.language, fan.channel, localizer.depth(fan), job.max_segments
    )
    if verify(msg, job.lead.facts, snap, job.max_segments).ok:
        return msg
    return Message(
        channel=fan.channel,
        title=msg.title,
        value=msg.value,
        language=fan.language,
        text=fit_text(msg.text, fan.channel, fan.language, job.max_segments),
    )
