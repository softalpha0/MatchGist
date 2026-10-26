"use client";

import { createContext, useContext } from "react";
import type { Delivery, Fan, MatchEvent } from "@/lib/types";
import type { StreamState } from "@/lib/useMatchStream";

/** What the drawer is showing: one delivered message, or one detected moment. */
export type Inspected = { delivery: Delivery } | { momentId: string } | null;

export const InspectContext = createContext<(item: Inspected) => void>(() => {});

/** The small "why?" link under every message. */
export function WhyButton({ d }: { d: Delivery }) {
  const inspect = useContext(InspectContext);
  return (
    <button onClick={() => inspect({ delivery: d })} className="text-sky-300 underline-offset-2 hover:underline" title="Show the events, facts and agent steps behind this message">
      {d.fallback_used ? "why? (template)" : "why? ✓ checked"}
    </button>
  );
}

const HIDDEN_FACTS = new Set(["home", "away", "home_code", "away_code"]);

function EventRow({ e, names }: { e: MatchEvent; names: Record<string, string> }) {
  return (
    <tr className="border-t border-line/60">
      <td className="py-1 pr-2 font-mono text-slate-400">{e.match_clock}</td>
      <td className="pr-2">{e.type.replace("_", " ")}</td>
      <td className="pr-2">{e.player_id ? names[e.player_id] ?? e.player_id : ""}</td>
      <td className="pr-2 text-slate-400">{e.team_id ?? ""}</td>
      <td className="pr-2 font-mono text-slate-500">{e.x != null && e.y != null ? `${e.x}, ${e.y}` : ""}</td>
      <td className="text-slate-500">{e.outcome ?? ""}</td>
    </tr>
  );
}

export function EvidenceDrawer({ item, state, model, onClose }: {
  item: Inspected;
  state: StreamState;
  model: string;
  onClose: () => void;
}) {
  if (!item) return null;
  const delivery = "delivery" in item ? item.delivery : null;
  const momentIds = delivery ? delivery.moment_ids : [(item as { momentId: string }).momentId];
  const moments = state.moments.filter((m) => momentIds.includes(m.moment_id));
  const fan: Fan | undefined = delivery ? state.fans.find((f) => f.fan_id === delivery.fan_id) : undefined;
  const steps = state.agentEvents.filter(
    (e) => e.moment_id && momentIds.includes(e.moment_id) && (!delivery || !e.fan_id || e.fan_id === delivery.fan_id),
  );
  const offline = model.startsWith("offline");

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/50" onClick={onClose}>
      <aside onClick={(e) => e.stopPropagation()}
        className="scrollbar-thin h-full w-full max-w-xl overflow-y-auto border-l border-line bg-panel p-4 text-sm shadow-2xl">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-[11px] uppercase tracking-wider text-slate-400">{delivery ? "Why this message" : "Why this moment matters"}</div>
            {fan && <div className="font-semibold">{fan.display_name} · {delivery?.channel} · {delivery?.language}</div>}
          </div>
          <button onClick={onClose} className="rounded-md border border-line px-2 py-1 text-xs hover:bg-panel-2">Close</button>
        </div>

        {delivery && (
          <section className="mt-3 rounded-xl border border-line bg-panel-2 p-3">
            {delivery.title && <div className="font-semibold">{delivery.title}</div>}
            <div dir={delivery.language === "ar" ? "rtl" : "ltr"}>{delivery.text}{delivery.value ? `  [${delivery.value}]` : ""}</div>
            <div className="mt-2 flex flex-wrap gap-2 text-[11px]">
              <span className="rounded bg-black/30 px-1.5 py-0.5">{delivery.size_kb} KB</span>
              {delivery.segments != null && <span className="rounded bg-black/30 px-1.5 py-0.5">{delivery.segments} SMS segment · {delivery.encoding}</span>}
              <span className={`rounded px-1.5 py-0.5 ${delivery.fallback_used ? "bg-amber-500/15 text-amber-300" : "bg-emerald-500/15 text-emerald-300"}`}>
                {delivery.fallback_used
                  ? "template fallback (model output failed a check or timed out)"
                  : `${offline ? "offline template backend" : "written by the model"}; Verifier passed: numbers from the facts, channel limits met`}
              </span>
              {delivery.attempts > 1 && <span className="rounded bg-black/30 px-1.5 py-0.5">{delivery.attempts} attempts</span>}
            </div>
            <div className="mt-2 text-[12px] text-slate-400">Budget Guard: {delivery.decision_reason}</div>
          </section>
        )}

        {moments.map((m) => {
          const sources = (m.source_event_ids ?? []).map((id) => state.eventIndex.get(id)).filter(Boolean) as MatchEvent[];
          const facts = Object.entries(m.facts).filter(([k]) => !HIDDEN_FACTS.has(k));
          return (
            <section key={m.moment_id} className="mt-4">
              <div className="font-semibold">{m.match_clock} · {m.type.replace("_", " ")} <span className="font-mono text-xs text-slate-500">score {m.base_score}</span></div>
              <div className="mt-2 text-[11px] uppercase tracking-wider text-slate-400">Detected facts (Stats Engine; the only numbers agents may use)</div>
              <table className="mt-1 w-full text-[12px]">
                <tbody>
                  {facts.map(([k, v]) => (
                    <tr key={k} className="border-t border-line/60">
                      <td className="py-1 pr-3 text-slate-400">{k.replaceAll("_", " ")}</td>
                      <td className="font-mono">{String(v)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="mt-3 text-[11px] uppercase tracking-wider text-slate-400">Source events (trigger last)</div>
              {sources.length ? (
                <table className="mt-1 w-full text-[12px]">
                  <tbody>{sources.map((e) => <EventRow key={e.event_id} e={e} names={state.names} />)}</tbody>
                </table>
              ) : (
                <div className="text-xs text-slate-500">Not available for this moment.</div>
              )}
            </section>
          );
        })}

        {steps.length > 0 && (
          <section className="mt-4">
            <div className="text-[11px] uppercase tracking-wider text-slate-400">Agent steps{delivery ? " for this fan" : ""}</div>
            <ol className="mt-1 space-y-1 text-[12px]">
              {steps.map((e, i) => (
                <li key={i} className="flex gap-2 border-t border-line/60 pt-1">
                  <span className="w-20 shrink-0 text-slate-400">{e.agent.replace("_", " ")}</span>
                  <span className="w-16 shrink-0">{e.action}</span>
                  <span className="min-w-0 flex-1 break-words text-slate-300">{e.detail}</span>
                  {e.latency_ms != null && <span className="shrink-0 font-mono text-slate-500">{e.latency_ms} ms</span>}
                </li>
              ))}
            </ol>
          </section>
        )}
        <div className="mt-4 text-[11px] text-slate-500">Agents: {model}. Synthetic match; all clubs, players and fans are fictional.</div>
      </aside>
    </div>
  );
}
