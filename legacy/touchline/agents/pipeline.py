"""Orchestration: two Microsoft Agent Framework workflows over one shared match state.

Live workflow (runs every broadcast tick, deterministic, never blocks on a model)::

    IngestAgent ──► InterpretAgent ──► DirectorAgent ──► overlay cues (revision 0)

Enrichment workflow (runs per key moment, concurrently, model-backed)::

                     ┌─ moment is HT/FT ─► NarratorAgent ─────────────────────┐
    Dispatcher ──────┤                                                          ├─► cue update (revision 1)
                     └─ otherwise ───────► AnalystAgent ─► PersonalizerAgent ─┘

Every model call goes through the Supervisor (timeout, budget, circuit
breaker) and the Verifier (no invented numbers). Failures fall back to the
deterministic template, so a cue is never left without text.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from agent_framework import Case, Default, Executor, WorkflowBuilder, WorkflowContext, handler

from touchline.agents import templates
from touchline.agents.backends import OFFLINE_MODEL, make_client
from touchline.agents.director import Director
from touchline.agents.ingest import IngestGate, IngestReport
from touchline.agents.roles import AgentTeam, ChaosControls, build_team, task_message
from touchline.agents.supervisor import Supervisor, Trace
from touchline.analytics.moments import MomentDetector
from touchline.analytics.state import MatchState
from touchline.config import Settings
from touchline.models import Frame, Insight, MatchEvent, MatchMeta, OverlayCue, Profile, Side

RECAP_KINDS = ("half_time", "full_time")


# --------------------------------------------------------------------------- messages
@dataclass
class FeedBatch:
    frames: list[Frame]
    raw_events: list[dict[str, Any]]


@dataclass
class CleanBatch:
    frames: list[Frame]
    events: list[MatchEvent]
    report: IngestReport


@dataclass
class InsightBatch:
    frame: Frame | None
    events: list[MatchEvent]
    insights: list[Insight]
    report: IngestReport


@dataclass
class LiveOutput:
    frame: Frame | None
    events: list[MatchEvent]
    insights: list[Insight]
    cues: list[OverlayCue]
    report: IngestReport


@dataclass
class EnrichRequest:
    insight: Insight
    profile: Profile


@dataclass
class Draft:
    request: EnrichRequest
    text: str
    from_model: bool


@dataclass
class CueUpdate:
    insight_id: str
    why: str
    profile_key: str
    traces: list[dict] = field(default_factory=list)


# --------------------------------------------------------------------------- live executors
class IngestAgent(Executor):
    def __init__(self, gate: IngestGate, supervisor: Supervisor):
        super().__init__(id="ingest")
        self.gate = gate
        self.supervisor = supervisor

    @handler
    async def ingest(self, batch: FeedBatch, ctx: WorkflowContext[CleanBatch]) -> None:
        events, report = self.gate.process(batch.raw_events)
        for note in report.notes:
            status = (
                "repaired"
                if note.startswith(("clamped", "re-sequenced", "accepted"))
                else "quarantined"
                if note.startswith("quarantined")
                else "dropped"
            )
            self.supervisor.record("ingest", "-", status, note)
        await ctx.send_message(CleanBatch(batch.frames, events, report))


class InterpretAgent(Executor):
    def __init__(self, state: MatchState, detector: MomentDetector):
        super().__init__(id="interpret")
        self.state = state
        self.detector = detector

    @handler
    async def interpret(self, batch: CleanBatch, ctx: WorkflowContext[InsightBatch]) -> None:
        insights: list[Insight] = []
        events = sorted(batch.events, key=lambda e: e.t)
        i = 0
        for frame in batch.frames:
            while i < len(events) and events[i].t <= frame.t:
                self.state.apply_event(events[i])
                insights.extend(self.detector.on_event(events[i]))
                i += 1
            started = self.state.apply_frame(frame)
            insights.extend(self.detector.on_sprints(started, frame.t))
            insights.extend(self.detector.on_clock(frame.t))
        for ev in events[i:]:
            self.state.apply_event(ev)
            insights.extend(self.detector.on_event(ev))
        last = batch.frames[-1] if batch.frames else None
        await ctx.send_message(InsightBatch(last, events, insights, batch.report))


class DirectorAgent(Executor):
    def __init__(self, director: Director):
        super().__init__(id="director")
        self.director = director

    @handler
    async def direct(self, batch: InsightBatch, ctx: WorkflowContext[None, LiveOutput]) -> None:
        cues = [c for c in (self.director.cue_for(i) for i in batch.insights) if c is not None]
        await ctx.yield_output(LiveOutput(batch.frame, batch.events, batch.insights, cues, batch.report))


# --------------------------------------------------------------------------- enrichment executors
class Dispatcher(Executor):
    def __init__(self) -> None:
        super().__init__(id="dispatcher")

    @handler
    async def dispatch(self, req: EnrichRequest, ctx: WorkflowContext[EnrichRequest]) -> None:
        await ctx.send_message(req)


def _facts_for_model(ins: Insight, lang: str) -> dict[str, Any]:
    facts = templates.derive(ins.facts, lang)
    facts.pop("pressure_text", None)
    return facts


class AnalystAgent(Executor):
    def __init__(self, team: AgentTeam, supervisor: Supervisor, use_model: Callable[[Insight], bool]):
        super().__init__(id="analyst")
        self.team = team
        self.supervisor = supervisor
        self.use_model = use_model

    @handler
    async def analyse(self, req: EnrichRequest, ctx: WorkflowContext[Draft]) -> None:
        ins = req.insight
        facts = _facts_for_model(ins, "en")

        def fallback() -> str:
            return templates.explain(ins.kind, ins.facts, "en", "analyst")

        if not self.use_model(ins):
            self.supervisor.record(
                "analyst", ins.id, "skipped", "below model importance threshold", "template"
            )
            await ctx.send_message(Draft(req, fallback(), False))
            return

        async def call() -> str:
            resp = await self.team.analyst.run(task_message("explain", kind=ins.kind, facts=facts))
            return resp.text or ""

        text, trace = await self.supervisor.run("analyst", ins.id, call, fallback, facts)
        await ctx.send_message(Draft(req, text, trace.status == "ok"))


class PersonalizerAgent(Executor):
    def __init__(self, team: AgentTeam, supervisor: Supervisor):
        super().__init__(id="personalizer")
        self.team = team
        self.supervisor = supervisor

    @handler
    async def personalise(self, draft: Draft, ctx: WorkflowContext[None, CueUpdate]) -> None:
        req = draft.request
        ins, p = req.insight, req.profile
        facts = _facts_for_model(ins, p.language)

        def fallback() -> str:
            return templates.explain(ins.kind, ins.facts, p.language, p.mode)

        neutral = (
            p.mode == "analyst" and p.language == "en" and not p.favourite_side and not p.focus_player_id
        )
        if not draft.from_model:
            # no model draft to adapt: render the profile directly from the facts
            self.supervisor.record(
                "personalizer", ins.id, "skipped", "no model draft: template rendered for profile", "template"
            )
            text = fallback()
        elif neutral:
            self.supervisor.record(
                "personalizer", ins.id, "skipped", "analyst draft already fits this profile", "-"
            )
            text = draft.text
        else:
            text, _ = await self.supervisor.run(
                "personalizer", ins.id, self._call(ins, p, facts, draft.text), fallback, facts
            )
        await ctx.yield_output(CueUpdate(ins.id, text, p.cache_key()))

    def _call(self, ins: Insight, p: Profile, facts: dict[str, Any], draft: str):
        async def call() -> str:
            resp = await self.team.personalizer.run(
                task_message(
                    "personalize", kind=ins.kind, facts=facts, draft=draft, profile=profile_payload(p, ins)
                )
            )
            return resp.text or ""

        return call


class NarratorAgent(Executor):
    def __init__(self, team: AgentTeam, supervisor: Supervisor, key_moments: Callable[[], list[dict]]):
        super().__init__(id="narrator")
        self.team = team
        self.supervisor = supervisor
        self.key_moments = key_moments

    @handler
    async def recap(self, req: EnrichRequest, ctx: WorkflowContext[None, CueUpdate]) -> None:
        ins, p = req.insight, req.profile
        facts = _facts_for_model(ins, p.language)
        moments = self.key_moments()

        def fallback() -> str:
            return templates.explain(ins.kind, ins.facts, p.language, p.mode)

        async def call() -> str:
            resp = await self.team.narrator.run(
                task_message(
                    "recap", kind=ins.kind, facts=facts, key_moments=moments, profile=profile_payload(p, ins)
                )
            )
            return resp.text or ""

        verify_facts = {**facts, "key_moments": moments}
        text, _ = await self.supervisor.run("narrator", ins.id, call, fallback, verify_facts)
        await ctx.yield_output(CueUpdate(ins.id, text, p.cache_key()))


def profile_payload(p: Profile, ins: Insight) -> dict[str, Any]:
    return {
        "mode": p.mode,
        "language": p.language,
        "favourite_club": ins.facts.get("team")
        if p.favourite_side and p.favourite_side == ins.side
        else None,
        "favourite_side": p.favourite_side.value if p.favourite_side else None,
        "focus_player": ins.facts.get("player")
        if p.focus_player_id and p.focus_player_id == ins.player_id
        else None,
    }


# --------------------------------------------------------------------------- facade
class MatchPipeline:
    """Owns the shared state and both workflows for one viewer session."""

    def __init__(
        self,
        meta: MatchMeta,
        profile: Profile,
        settings: Settings,
        on_trace: Callable[[Trace], None] | None = None,
        client: Any | None = None,
        model_label: str | None = None,
    ):
        self.settings = settings
        self.state = MatchState(meta)
        self.detector = MomentDetector(self.state)
        self.director = Director(profile)
        if client is None:
            client, model_label = make_client(settings)
        self.model_label = model_label or OFFLINE_MODEL
        self.supervisor = Supervisor(
            model_label=self.model_label,
            timeout_s=settings.llm_timeout_s,
            budget=settings.llm_budget_per_session if self.model_label != OFFLINE_MODEL else 10**9,
            breaker_failures=settings.breaker_failures,
            breaker_cooldown_s=settings.breaker_cooldown_s,
            concurrency=settings.llm_concurrency,
            on_trace=on_trace,
        )
        self.chaos = ChaosControls()
        self.team = build_team(client, self.model_label, self.chaos)
        self.gate = IngestGate({p.id for p in meta.players})
        self.insights: dict[str, Insight] = {}
        self.counters = {"events": 0, "insights": 0, "cues": 0}

        ingest = IngestAgent(self.gate, self.supervisor)
        interpret = InterpretAgent(self.state, self.detector)
        direct = DirectorAgent(self.director)
        self.live = (
            WorkflowBuilder(name="touchline-live", start_executor=ingest)
            .add_chain([ingest, interpret, direct])
            .build()
        )

    @property
    def profile(self) -> Profile:
        return self.director.profile

    def set_profile(self, profile: Profile) -> None:
        self.director.profile = profile
        self.director.on_air.clear()

    def use_model(self, ins: Insight) -> bool:
        if self.model_label == OFFLINE_MODEL:
            return True
        return ins.importance >= self.settings.llm_min_importance or (
            self.profile.focus_player_id is not None and ins.player_id == self.profile.focus_player_id
        )

    def key_moments(self) -> list[dict]:
        keep = ("goal", "big_chance", "momentum_swing", "card", "control_shift")
        return [
            {
                "kind": i.kind,
                "minute": i.facts.get("minute"),
                "team": i.facts.get("team"),
                "player": i.facts.get("player"),
            }
            for i in self.insights.values()
            if i.kind in keep
        ][-12:]

    def _enrichment_workflow(self):
        dispatcher = Dispatcher()
        analyst = AnalystAgent(self.team, self.supervisor, self.use_model)
        personalizer = PersonalizerAgent(self.team, self.supervisor)
        narrator = NarratorAgent(self.team, self.supervisor, self.key_moments)
        return (
            WorkflowBuilder(name="touchline-enrich", start_executor=dispatcher)
            .add_switch_case_edge_group(
                dispatcher,
                [
                    Case(condition=lambda r: r.insight.kind in RECAP_KINDS, target=narrator),
                    Default(target=analyst),
                ],
            )
            .add_edge(analyst, personalizer)
            .build()
        )

    async def tick(self, frames: list[Frame], raw_events: list[dict[str, Any]]) -> LiveOutput:
        result = await self.live.run(FeedBatch(frames, raw_events))
        out: LiveOutput = result.get_outputs()[0]
        for ins in out.insights:
            self.insights[ins.id] = ins
        self.counters["events"] += len(out.events)
        self.counters["insights"] += len(out.insights)
        self.counters["cues"] += len(out.cues)
        return out

    async def enrich(self, insight: Insight, profile: Profile | None = None) -> CueUpdate | None:
        req = EnrichRequest(insight, profile or self.profile)
        result = await self._enrichment_workflow().run(req)
        outputs = result.get_outputs()
        return outputs[0] if outputs else None

    def recent_insights(self, n: int = 8) -> list[Insight]:
        return list(self.insights.values())[-n:]

    def side_name(self, side: Side) -> str:
        return (self.state.meta.home if side is Side.HOME else self.state.meta.away).name
