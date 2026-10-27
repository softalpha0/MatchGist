"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AddFan } from "@/components/AddFan";
import { Device } from "@/components/Devices";
import { EvidenceDrawer, InspectContext, type Inspected } from "@/components/Evidence";
import { Logo } from "@/components/Logo";
import { Pitch, StatStrip } from "@/components/Pitch";
import { SystemPanel } from "@/components/SystemPanel";
import { getConfig, startReplay } from "@/lib/api";
import type { MatchEvent } from "@/lib/types";
import { type Source, useMatchFeed } from "@/lib/useMatchStream";

const STORYLINES: [string, string][] = [
  ["late_drama", "Late drama"],
  ["comeback", "Comeback"],
  ["red_card", "Red card"],
  ["none", "Open game"],
];
const SPEEDS = [1, 10, 30, 60, 120];

const MOMENT_LABEL: Record<string, string> = {
  goal: "Goal",
  red_card: "Red card",
  yellow_card: "Yellow",
  big_chance: "Big chance",
  momentum_swing: "Momentum swing",
  pressure_spike: "Pressure spike",
  elite_pass: "Elite pass",
  half_time: "Half-time",
  full_time: "Full-time",
};

const clockSeconds = (e: MatchEvent) => {
  const [m, s] = e.match_clock.split(":").map(Number);
  return m * 60 + s;
};
const JUMPS: [string, (e: MatchEvent) => boolean][] = [
  ["HT", (e) => e.type === "half_time"],
  ["60'", (e) => e.period === 2 && clockSeconds(e) >= 59 * 60],
  ["75'", (e) => e.period === 2 && clockSeconds(e) >= 74 * 60],
  ["85'", (e) => e.period === 2 && clockSeconds(e) >= 84 * 60],
  ["FT", (e) => e.type === "full_time"],
];

type Mode = "checking" | "live" | "replay";

export default function LivePage() {
  const [storyline, setStoryline] = useState("late_drama");
  const [speed, setSpeed] = useState(30);
  const [source, setSource] = useState<Source>(null);
  const [mode, setMode] = useState<Mode>("checking");
  const [preferRecorded, setPreferRecorded] = useState(false);
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [model, setModel] = useState<string>("");
  const [inspected, setInspected] = useState<Inspected>(null);
  const { state: s, jump, meta } = useMatchFeed(source, speed);

  useEffect(() => {
    // with the API server: live agents. As a static site (e.g. Netlify): recorded matches, no server needed
    const timeout = new Promise<never>((_, reject) => setTimeout(() => reject(new Error("timeout")), 2500));
    Promise.race([getConfig(), timeout])
      .then((c) => {
        setModel(c.model);
        setMode("live");
      })
      .catch(() => setMode("replay"));
  }, []);

  const replaying = mode === "replay" || preferRecorded;

  async function kickOff() {
    setStartError(null);
    setInspected(null);
    if (replaying) {
      setSource({ kind: "replay", storyline, run: Date.now() });
      return;
    }
    setStarting(true);
    try {
      const info = await startReplay(storyline, speed);
      setSource({ kind: "live", matchId: info.match_id });
    } catch (e) {
      setStartError(String(e).includes("404") ? "Demo matches are still being prepared. Try again in a few seconds." : String(e));
    } finally {
      setStarting(false);
    }
  }

  const snap = s.snapshot;
  const agentsLabel = (replaying ? meta?.model : model) || snap?.model || model;
  const deviceFans = s.fans.filter((f) => f.channel !== "broadcast");
  const broadcastFan = s.fans.find((f) => f.channel === "broadcast");
  const overlays = broadcastFan ? s.deliveries[broadcastFan.fan_id] ?? [] : [];
  const keyMoments = useMemo(() => s.moments.filter((m) => m.base_score >= 50).slice(-8).reverse(), [s.moments]);
  const statusLabel = !snap
    ? ""
    : snap.status === "full_time"
      ? "FT"
      : snap.status === "half_time"
        ? "HT"
        : snap.status === "pre_match"
          ? "KO"
          : snap.match_clock;

  return (
    <InspectContext.Provider value={setInspected}>
      <div className="flex min-h-screen flex-col lg:h-screen lg:min-h-[700px]">
        {/* top bar: scoreboard, controls */}
        <header className="flex shrink-0 flex-wrap items-center gap-x-4 gap-y-2 border-b border-line bg-panel px-4 py-2 lg:h-16 lg:flex-nowrap lg:py-0">
          <Link href="/"><Logo /></Link>
          <div className="flex items-center gap-2 lg:mx-auto lg:gap-3">
            <span className="text-xs font-semibold text-riv sm:text-sm">{snap?.home.name ?? "Riverside Athletic"}</span>
            <span className="rounded-md bg-black px-2 py-1 font-mono text-xl font-bold tabular-nums sm:px-3 sm:text-2xl">
              {snap ? `${snap.score[0]} – ${snap.score[1]}` : "0 – 0"}
            </span>
            <span className="text-xs font-semibold text-nor sm:text-sm">{snap?.away.name ?? "Northgate Rovers"}</span>
            <span className="rounded bg-accent/15 px-2 py-0.5 font-mono text-sm text-accent">{statusLabel || "–"}</span>
            {snap && (snap.home.players_on_pitch < 11 || snap.away.players_on_pitch < 11) && (
              <span className="rounded bg-red-500/20 px-1.5 py-0.5 text-[11px] text-red-300">
                {snap.home.players_on_pitch}v{snap.away.players_on_pitch}
              </span>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <select value={storyline} onChange={(e) => setStoryline(e.target.value)} className="rounded-md border border-line bg-panel-2 px-2 py-1.5">
              {STORYLINES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
            <div className="flex overflow-hidden rounded-md border border-line">
              {SPEEDS.map((v) => (
                <button key={v} onClick={() => setSpeed(v)} disabled={!replaying && !!source}
                  title={!replaying && source ? "Speed is set when a live match starts" : undefined}
                  className={`px-2 py-1.5 ${speed === v ? "bg-accent text-ink" : "bg-panel-2 text-slate-300"}`}>
                  {v}x
                </button>
              ))}
            </div>
            <button onClick={kickOff} disabled={starting || mode === "checking"} className="rounded-md bg-accent px-3 py-1.5 font-semibold text-ink disabled:opacity-50">
              {source ? "Restart" : "Kick off"}
            </button>
            {replaying && source && jump && (
              <div className="flex items-center gap-1">
                <span className="text-slate-500">Jump:</span>
                {JUMPS.map(([label, match]) => (
                  <button key={label} onClick={() => jump(match)} className="rounded border border-line px-1.5 py-1 hover:bg-panel-2">{label}</button>
                ))}
              </div>
            )}
            {!replaying && (
              <button onClick={() => setAdding(true)} disabled={!source || s.ended}
                className="rounded-md border border-line px-3 py-1.5 text-slate-200 hover:bg-panel-2 disabled:opacity-40">
                + Add a fan
              </button>
            )}
          </div>
        </header>

        {s.ended && (
          <div className="bg-accent px-4 py-1 text-center text-[12px] font-semibold text-ink">
            Full time · digests sized to each fan&apos;s remaining budget · tap “why?” under any message for its evidence
          </div>
        )}

        {!source ? (
          <div className="flex flex-1 items-center justify-center p-4 sm:p-6">
            <div className="max-w-xl rounded-2xl border border-line bg-panel p-6 text-center shadow-2xl sm:p-8">
              <div className="text-2xl font-semibold">One match. Six fans. Six very different budgets.</div>
              <p className="mt-3 text-sm text-slate-400">
                A synthetic match between two fictional clubs plays at {speed}x. Each moment is explained once, then
                ranked, budgeted, translated and squeezed to fit an SMS, a voice note, a watch, a push alert and a
                broadcast overlay. Every decision shows in the System panel, and “why?” under any message shows the
                events and facts behind it.
              </p>
              <div className="mt-5 flex flex-wrap justify-center gap-2">
                {STORYLINES.map(([v, l]) => (
                  <button key={v} onClick={() => setStoryline(v)}
                    className={`rounded-full px-3 py-1 text-sm ${storyline === v ? "bg-accent text-ink" : "bg-panel-2 text-slate-300"}`}>
                    {l}
                  </button>
                ))}
              </div>
              <button onClick={kickOff} disabled={starting || mode === "checking"}
                className="mt-6 rounded-xl bg-accent px-6 py-3 text-lg font-semibold text-ink shadow-lg shadow-lime-500/20 disabled:opacity-50">
                {starting ? "Preparing…" : mode === "checking" ? "Loading…" : "Kick off"}
              </button>
              {startError && <div className="mt-3 text-xs text-amber-300">{startError}</div>}
              <div className="mt-4 text-[11px] text-slate-500">
                {mode === "replay"
                  ? "Recorded runs of the full agent pipeline (no server needed). Use Jump to skip ahead."
                  : mode === "live"
                    ? `Live agents: ${model || "…"}`
                    : "Checking for the agent server…"}
                {" · all clubs, players and fans are fictional"}
              </div>
              {mode === "live" && (
                <label className="mt-2 flex items-center justify-center gap-2 text-[11px] text-slate-400">
                  <input type="checkbox" checked={preferRecorded} onChange={(e) => setPreferRecorded(e.target.checked)} />
                  play a recorded run instead (instant, with Jump)
                </label>
              )}
            </div>
          </div>
        ) : (
          <main className="flex flex-col gap-3 p-3 lg:grid lg:min-h-0 lg:flex-1 lg:grid-cols-[minmax(0,30fr)_minmax(0,46fr)_minmax(0,24fr)]">
            {/* left: pitch with the analyst overlay, stats, key moments */}
            <section className="flex min-h-0 flex-col gap-3">
              <Pitch snapshot={snap} events={s.events} overlays={overlays} speed={replaying ? speed : snap?.speed ?? speed} names={s.names} />
              <StatStrip snapshot={snap} />
              <div className="min-h-0 flex-1 overflow-hidden rounded-xl border border-line bg-panel p-3">
                <div className="mb-2 text-[11px] uppercase tracking-wider text-slate-400">Key moments · tap for evidence</div>
                <div className="space-y-1.5">
                  {keyMoments.length === 0 && <div className="text-xs text-slate-500">Nothing big yet.</div>}
                  {keyMoments.map((m) => (
                    <button key={m.moment_id} onClick={() => setInspected({ momentId: m.moment_id })}
                      className="animate-pop flex w-full items-center gap-2 rounded text-left text-xs hover:bg-panel-2">
                      <span className="w-12 font-mono text-slate-500">{m.match_clock}</span>
                      <span className={`rounded px-1.5 py-px ${m.type === "goal" ? "bg-accent/20 text-accent" : "bg-slate-700/60 text-slate-200"}`}>
                        {MOMENT_LABEL[m.type] ?? m.type}
                      </span>
                      <span className="truncate text-slate-300">{String(m.facts.player ?? m.facts.team ?? m.facts.pressing_team ?? "")}</span>
                      <span className="ml-auto font-mono text-slate-500">{m.base_score}</span>
                    </button>
                  ))}
                </div>
              </div>
            </section>

            {/* centre: one device per fan */}
            <section className="scrollbar-thin grid auto-rows-[400px] grid-cols-1 gap-3 sm:grid-cols-2 lg:min-h-0 lg:auto-rows-[minmax(0,1fr)] lg:grid-cols-3 lg:overflow-y-auto"
              style={{ gridTemplateRows: deviceFans.length > 6 ? "repeat(auto-fill, 420px)" : undefined }}>
              {deviceFans.map((f) => (
                <Device key={f.fan_id} fan={f} ledger={s.ledgers[f.fan_id]} deliveries={s.deliveries[f.fan_id] ?? []} />
              ))}
              {!replaying && !s.ended && deviceFans.length % 3 !== 0 && (
                <button onClick={() => setAdding(true)}
                  className="hidden flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-line text-slate-400 hover:border-accent/50 hover:text-accent lg:flex">
                  <span className="text-3xl">+</span>
                  <span className="text-sm font-semibold">Add a fan</span>
                  <span className="max-w-[16rem] text-center text-xs text-slate-500">Pick a language, channel and budget, and watch them join live.</span>
                </button>
              )}
            </section>

            {/* right: agent decisions */}
            <section className="h-[520px] min-h-0 lg:h-auto">
              <SystemPanel events={s.agentEvents} fans={s.fans} model={agentsLabel} />
            </section>
          </main>
        )}
        {adding && source?.kind === "live" && <AddFan matchId={source.matchId} onClose={() => setAdding(false)} />}
        <EvidenceDrawer item={inspected} state={s} model={agentsLabel || ""} onClose={() => setInspected(null)} />
      </div>
    </InspectContext.Provider>
  );
}
