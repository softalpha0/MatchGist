"use client";

import { useMemo, useState } from "react";
import type { AgentEvent, Fan } from "@/lib/types";

const AGENT_COLOR: Record<string, string> = {
  explainer: "bg-sky-500/15 text-sky-300",
  ranker: "bg-slate-500/20 text-slate-300",
  budget_guard: "bg-amber-500/15 text-amber-300",
  localizer: "bg-violet-500/15 text-violet-300",
  compressor: "bg-teal-500/15 text-teal-300",
  verifier: "bg-emerald-500/15 text-emerald-300",
  digest: "bg-lime-500/15 text-lime-300",
  voice: "bg-fuchsia-500/15 text-fuchsia-300",
};

const FILTERS = {
  decisions: (e: AgentEvent) => e.agent === "budget_guard" || (e.agent === "verifier" && e.action !== "pass") || e.action === "fallback",
  all: () => true,
  verifier: (e: AgentEvent) => e.agent === "verifier" || e.agent === "compressor",
  fallbacks: (e: AgentEvent) => e.action === "fallback" || e.action === "reject",
} as const;

export function SystemPanel({ events, fans, model }: { events: AgentEvent[]; fans: Fan[]; model?: string }) {
  const [filter, setFilter] = useState<keyof typeof FILTERS>("decisions");
  const [fanFilter, setFanFilter] = useState<string>("");
  const names = useMemo(() => Object.fromEntries(fans.map((f) => [f.fan_id, f.display_name.split(",")[0]])), [fans]);
  const shown = events.filter((e) => FILTERS[filter](e) && (!fanFilter || e.fan_id === fanFilter)).slice(-160).reverse();
  const counts = {
    rejects: events.filter((e) => e.action === "reject").length,
    fallbacks: events.filter((e) => e.action === "fallback").length,
    holds: events.filter((e) => e.agent === "budget_guard" && e.action === "hold").length,
    skips: events.filter((e) => e.agent === "budget_guard" && e.action === "skip").length,
  };

  return (
    <div className="flex h-full min-h-0 flex-col rounded-xl border border-line bg-panel">
      <div className="border-b border-line p-3">
        <div className="flex items-center justify-between">
          <div className="text-sm font-semibold">System panel</div>
          <span className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-400">{model ?? "…"}</span>
        </div>
        <div className="mt-2 grid grid-cols-4 gap-1.5 text-center text-[10px]">
          {(
            [
              ["skips", counts.skips, "text-slate-300"],
              ["holds", counts.holds, "text-accent-2"],
              ["rejects", counts.rejects, "text-amber-300"],
              ["fallbacks", counts.fallbacks, "text-orange-300"],
            ] as const
          ).map(([k, v, c]) => (
            <div key={k} className="rounded bg-panel-2 py-1">
              <div className={`font-mono text-base ${c}`}>{v}</div>
              <div className="text-slate-500">{k}</div>
            </div>
          ))}
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-1">
          {(Object.keys(FILTERS) as (keyof typeof FILTERS)[]).map((f) => (
            <button key={f} onClick={() => setFilter(f)}
              className={`rounded px-2 py-0.5 text-[11px] ${filter === f ? "bg-accent text-ink" : "bg-panel-2 text-slate-300 hover:bg-slate-700"}`}>
              {f}
            </button>
          ))}
          <select value={fanFilter} onChange={(e) => setFanFilter(e.target.value)}
            className="ml-auto rounded bg-panel-2 px-1.5 py-0.5 text-[11px] text-slate-300">
            <option value="">all fans</option>
            {fans.map((f) => <option key={f.fan_id} value={f.fan_id}>{names[f.fan_id]}</option>)}
          </select>
        </div>
      </div>
      <div className="scrollbar-thin min-h-0 flex-1 space-y-1 overflow-y-auto p-2">
        {shown.length === 0 && <div className="p-4 text-center text-xs text-slate-500">Agent decisions appear here as the match runs.</div>}
        {shown.map((e, i) => (
          <div key={`${e.ts}-${i}`} className="animate-pop rounded-md bg-panel-2/70 px-2 py-1.5 text-[11px]">
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-slate-500">{e.match_clock}</span>
              <span className={`rounded px-1.5 py-px font-medium ${AGENT_COLOR[e.agent] ?? "bg-slate-700 text-slate-200"}`}>{e.agent.replace("_", " ")}</span>
              <span className={`font-semibold ${e.action === "reject" || e.action === "fallback" ? "text-amber-300" : e.action === "skip" ? "text-slate-400" : "text-slate-100"}`}>
                {e.action}
              </span>
              {e.fan_id && <span className="ml-auto truncate text-slate-500">{names[e.fan_id] ?? e.fan_id}</span>}
            </div>
            <div className="mt-0.5 break-words text-slate-300">{e.detail}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
