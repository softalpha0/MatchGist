"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AddFan } from "@/components/AddFan";
import { Device } from "@/components/Devices";
import { Logo } from "@/components/Logo";
import { Pitch, StatStrip } from "@/components/Pitch";
import { SystemPanel } from "@/components/SystemPanel";
import { getConfig, startReplay } from "@/lib/api";
import { useMatchStream } from "@/lib/useMatchStream";

const STORYLINES: [string, string][] = [
  ["late_drama", "Late drama"],
  ["comeback", "Comeback"],
  ["red_card", "Red card"],
  ["none", "Open game"],
];
const SPEEDS = [10, 30, 60, 120];

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

export default function LivePage() {
  const [storyline, setStoryline] = useState("late_drama");
  const [speed, setSpeed] = useState(30);
  const [matchId, setMatchId] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [model, setModel] = useState<string>("");
  const s = useMatchStream(matchId);

  useEffect(() => {
    getConfig().then((c) => setModel(c.model)).catch(() => setModel("api offline"));
  }, []);

  async function kickOff() {
    setStarting(true);
    setStartError(null);
    try {
      const info = await startReplay(storyline, speed);
      setMatchId(info.match_id);
    } catch (e) {
      setStartError(String(e).includes("404") ? "Demo matches are still being prepared. Try again in a few seconds." : String(e));
    } finally {
      setStarting(false);
    }
  }

  const snap = s.snapshot;
  const deviceFans = s.fans.filter((f) => f.channel !== "broadcast");
  const broadcastFan = s.fans.find((f) => f.channel === "broadcast");
  const overlays = broadcastFan ? s.deliveries[broadcastFan.fan_id] ?? [] : [];
  const keyMoments = useMemo(() => s.moments.filter((m) => m.base_score >= 50).slice(-6).reverse(), [s.moments]);
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
    <div className="flex h-screen min-h-[700px] flex-col">
      {/* top bar: scoreboard, controls */}
      <header className="flex h-16 shrink-0 items-center gap-4 border-b border-line bg-panel px-4">
        <Link href="/"><Logo /></Link>
        <div className="mx-auto flex items-center gap-3">
          <span className="text-sm font-semibold text-riv">{snap?.home.name ?? "Riverside Athletic"}</span>
          <span className="rounded-md bg-black px-3 py-1 font-mono text-2xl font-bold tabular-nums">
            {snap ? `${snap.score[0]} – ${snap.score[1]}` : "0 – 0"}
          </span>
          <span className="text-sm font-semibold text-nor">{snap?.away.name ?? "Northgate Rovers"}</span>
          <span className="ml-1 rounded bg-accent/15 px-2 py-0.5 font-mono text-sm text-accent">{statusLabel || "–"}</span>
          {s.ended && (
            <span className="rounded bg-accent px-2 py-0.5 text-[11px] font-semibold text-ink">
              Full time · digests sized to each fan&apos;s remaining budget
            </span>
          )}
          {snap && (snap.home.players_on_pitch < 11 || snap.away.players_on_pitch < 11) && (
            <span className="rounded bg-red-500/20 px-1.5 py-0.5 text-[11px] text-red-300">
              {snap.home.players_on_pitch}v{snap.away.players_on_pitch}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs">
          <select value={storyline} onChange={(e) => setStoryline(e.target.value)} className="rounded-md border border-line bg-panel-2 px-2 py-1.5">
            {STORYLINES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
          <div className="flex overflow-hidden rounded-md border border-line">
            {SPEEDS.map((v) => (
              <button key={v} onClick={() => setSpeed(v)} className={`px-2 py-1.5 ${speed === v ? "bg-accent text-ink" : "bg-panel-2 text-slate-300"}`}>
                {v}x
              </button>
            ))}
          </div>
          <button onClick={kickOff} disabled={starting} className="rounded-md bg-accent px-3 py-1.5 font-semibold text-ink disabled:opacity-50">
            {matchId ? "Restart" : "Kick off"}
          </button>
          <button onClick={() => setAdding(true)} disabled={!matchId || s.ended}
            className="rounded-md border border-line px-3 py-1.5 text-slate-200 hover:bg-panel-2 disabled:opacity-40">
            + Add a fan
          </button>
        </div>
      </header>

      {!matchId ? (
        <div className="flex flex-1 items-center justify-center p-6">
          <div className="max-w-xl rounded-2xl border border-line bg-panel p-8 text-center shadow-2xl">
            <div className="text-2xl font-semibold">One match. Six fans. Six very different budgets.</div>
            <p className="mt-3 text-sm text-slate-400">
              A synthetic match between two fictional clubs plays at {speed}x. Watch each moment get explained once, then
              ranked, budgeted, translated and squeezed to fit an SMS, a voice note, a watch, a push alert and a broadcast
              overlay, with every decision in the System panel.
            </p>
            <div className="mt-5 flex flex-wrap justify-center gap-2">
              {STORYLINES.map(([v, l]) => (
                <button key={v} onClick={() => setStoryline(v)}
                  className={`rounded-full px-3 py-1 text-sm ${storyline === v ? "bg-accent text-ink" : "bg-panel-2 text-slate-300"}`}>
                  {l}
                </button>
              ))}
            </div>
            <button onClick={kickOff} disabled={starting}
              className="mt-6 rounded-xl bg-accent px-6 py-3 text-lg font-semibold text-ink shadow-lg shadow-lime-500/20 disabled:opacity-50">
              {starting ? "Preparing…" : "Kick off"}
            </button>
            {startError && <div className="mt-3 text-xs text-amber-300">{startError}</div>}
            <div className="mt-4 text-[11px] text-slate-500">Agents: {model || "…"} · all clubs, players and fans are fictional</div>
          </div>
        </div>
      ) : (
        <main className="grid min-h-0 flex-1 grid-cols-[minmax(0,30fr)_minmax(0,46fr)_minmax(0,24fr)] gap-3 p-3">
          {/* left: pitch with the analyst overlay, stats, key moments */}
          <section className="flex min-h-0 flex-col gap-3">
            <Pitch snapshot={snap} events={s.events} overlays={overlays} speed={snap?.speed ?? speed} />
            <StatStrip snapshot={snap} />
            <div className="min-h-0 flex-1 overflow-hidden rounded-xl border border-line bg-panel p-3">
              <div className="mb-2 text-[11px] uppercase tracking-wider text-slate-400">Key moments</div>
              <div className="space-y-1.5">
                {keyMoments.length === 0 && <div className="text-xs text-slate-500">Nothing big yet.</div>}
                {keyMoments.map((m) => (
                  <div key={m.moment_id} className="animate-pop flex items-center gap-2 text-xs">
                    <span className="w-12 font-mono text-slate-500">{m.match_clock}</span>
                    <span className={`rounded px-1.5 py-px ${m.type === "goal" ? "bg-accent/20 text-accent" : "bg-slate-700/60 text-slate-200"}`}>
                      {MOMENT_LABEL[m.type] ?? m.type}
                    </span>
                    <span className="truncate text-slate-300">{String(m.facts.player ?? m.facts.team ?? m.facts.pressing_team ?? "")}</span>
                    <span className="ml-auto font-mono text-slate-500">{m.base_score}</span>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* centre: one device per fan */}
          <section className="scrollbar-thin grid min-h-0 auto-rows-[minmax(0,1fr)] grid-cols-3 gap-3 overflow-y-auto"
            style={{ gridTemplateRows: deviceFans.length > 6 ? "repeat(auto-fill, 420px)" : undefined }}>
            {deviceFans.map((f) => (
              <Device key={f.fan_id} fan={f} ledger={s.ledgers[f.fan_id]} deliveries={s.deliveries[f.fan_id] ?? []} />
            ))}
            {!s.ended && deviceFans.length % 3 !== 0 && (
              <button onClick={() => setAdding(true)}
                className="flex flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-line text-slate-400 hover:border-accent/50 hover:text-accent">
                <span className="text-3xl">+</span>
                <span className="text-sm font-semibold">Add a fan</span>
                <span className="max-w-[16rem] text-center text-xs text-slate-500">Pick a language, channel and budget, and watch them join live.</span>
              </button>
            )}
          </section>

          {/* right: agent decisions */}
          <section className="min-h-0">
            <SystemPanel events={s.agentEvents} fans={s.fans} model={snap?.model ?? model} />
          </section>
        </main>
      )}
      {adding && matchId && <AddFan matchId={matchId} onClose={() => setAdding(false)} />}
    </div>
  );
}
