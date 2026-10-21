"use client";

import { useEffect, useState } from "react";
import type { Delivery, MatchEvent, Snapshot } from "@/lib/types";

const L = 105;
const W = 68;

/** Team-relative event coordinates -> broadcast view (home attacks right in the first half). */
function toAbs(e: MatchEvent, homeId: string, x: number, y: number): [number, number] {
  const attacksRight = (e.team_id === homeId) === (e.period === 1);
  return attacksRight ? [x, y] : [L - x, W - y];
}

const SLOT_CLASS: Record<string, string> = {
  top_bar: "left-1/2 top-3 -translate-x-1/2 w-[86%]",
  lower_third: "left-1/2 bottom-3 -translate-x-1/2 w-[86%]",
  side_panel: "right-3 top-1/2 -translate-y-1/2 w-[42%]",
  player_tag: "left-3 bottom-3 w-[56%]",
};

export function Pitch({ snapshot, events, overlays, speed }: {
  snapshot: Snapshot | null;
  events: MatchEvent[];
  overlays: Delivery[];
  speed: number;
}) {
  const homeId = snapshot?.home.club_id ?? "RIV";
  const [visible, setVisible] = useState<Delivery | null>(null);
  const last = overlays[overlays.length - 1];

  useEffect(() => {
    if (!last?.overlay) return;
    setVisible(last);
    // show for the cue's duration at playback speed, but long enough to read on a recording
    const ms = Math.min(9000, Math.max(3500, last.overlay.duration_ms / Math.max(speed, 1)));
    const t = setTimeout(() => setVisible(null), ms);
    return () => clearTimeout(t);
  }, [last, speed]);

  const shown = events.filter((e) => e.x != null && e.y != null).slice(-14);
  const lastEv = shown[shown.length - 1];

  return (
    <div className="relative w-full overflow-hidden rounded-xl border border-line" style={{ aspectRatio: `${L} / ${W}` }}>
      <svg viewBox={`-2 -2 ${L + 4} ${W + 4}`} className="absolute inset-0 h-full w-full">
        <rect x={-2} y={-2} width={L + 4} height={W + 4} fill="#0f3d2a" />
        {Array.from({ length: 7 }).map((_, i) => (
          <rect key={i} x={i * 15} y={0} width={7.5} height={W} fill="#114530" />
        ))}
        <g stroke="#4f8f6c" strokeWidth={0.35} fill="none">
          <rect x={0} y={0} width={L} height={W} />
          <line x1={L / 2} y1={0} x2={L / 2} y2={W} />
          <circle cx={L / 2} cy={W / 2} r={9.15} />
          <rect x={0} y={W / 2 - 20.16} width={16.5} height={40.32} />
          <rect x={L - 16.5} y={W / 2 - 20.16} width={16.5} height={40.32} />
          <rect x={0} y={W / 2 - 9.16} width={5.5} height={18.32} />
          <rect x={L - 5.5} y={W / 2 - 9.16} width={5.5} height={18.32} />
        </g>
        {shown.map((e, i) => {
          const [x, y] = toAbs(e, homeId, e.x!, e.y!);
          const color = e.team_id === homeId ? "#3b82f6" : "#ef4444";
          const opacity = 0.25 + (0.75 * (i + 1)) / shown.length;
          const end = e.end_x != null && e.end_y != null ? toAbs(e, homeId, e.end_x, e.end_y) : null;
          return (
            <g key={e.event_id} opacity={opacity}>
              {end && (e.type === "pass" || e.type === "carry") && (
                <line x1={x} y1={y} x2={end[0]} y2={end[1]} stroke={color} strokeWidth={0.5}
                  strokeDasharray={e.type === "carry" ? "1 1" : undefined} />
              )}
              <circle cx={x} cy={y} r={e.type === "shot" ? 1.6 : 1} fill={color} />
            </g>
          );
        })}
        {lastEv && (() => {
          const e = lastEv;
          const [x, y] = e.end_x != null && e.type === "pass" ? toAbs(e, homeId, e.end_x, e.end_y!) : toAbs(e, homeId, e.x!, e.y!);
          return <circle cx={x} cy={y} r={1.3} fill="#fff" stroke="#000" strokeWidth={0.3} />;
        })()}
      </svg>

      {visible?.overlay && (
        <div key={visible.delivery_id}
          className={`animate-pop absolute ${SLOT_CLASS[visible.overlay.slot] ?? SLOT_CLASS.lower_third} rounded-lg border border-white/10 bg-black/75 px-3 py-2 backdrop-blur`}>
          <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-accent">
            <span>{visible.overlay.template.replace("_", " ")}</span>
            <span className="text-slate-400">{visible.overlay.match_clock}</span>
            <span className="ml-auto rounded bg-white/10 px-1.5 text-slate-300">{visible.overlay.slot.replace("_", " ")}</span>
          </div>
          <div className="mt-0.5 text-[13px] leading-snug text-white">{visible.text}</div>
        </div>
      )}
      <div className="absolute left-3 top-3 rounded bg-black/50 px-2 py-0.5 text-[10px] text-slate-300">
        Analyst overlay · London
      </div>
    </div>
  );
}

export function StatStrip({ snapshot }: { snapshot: Snapshot | null }) {
  if (!snapshot) return null;
  const { home: h, away: a } = snapshot;
  const rows: [string, string | number | null, string | number | null][] = [
    ["Possession %", h.possession, a.possession],
    ["xG", h.xg, a.xg],
    ["Shots (on target)", `${h.shots} (${h.shots_on_target})`, `${a.shots} (${a.shots_on_target})`],
    ["Pass accuracy %", h.pass_accuracy, a.pass_accuracy],
    ["Pressure on passes", h.pressure_index, a.pressure_index],
  ];
  const m = snapshot.momentum;
  return (
    <div className="rounded-xl border border-line bg-panel p-3 text-xs">
      <div className="mb-2 flex items-center justify-between text-[11px] text-slate-400">
        <span>Momentum (last 5 min)</span>
        <span className="font-mono text-slate-200">{m > 0 ? `${h.club_id} +${m}` : m < 0 ? `${a.club_id} +${-m}` : "even"}</span>
      </div>
      <div className="relative mb-3 h-2 rounded-full bg-slate-800">
        <div className="absolute top-0 h-2 rounded-full bg-riv" style={{ left: "50%", width: `${Math.max(0, m) / 2}%` }} />
        <div className="absolute top-0 h-2 rounded-full bg-nor" style={{ right: "50%", width: `${Math.max(0, -m) / 2}%` }} />
        <div className="absolute left-1/2 top-[-2px] h-3 w-px bg-slate-400" />
      </div>
      <table className="w-full">
        <tbody>
          {rows.map(([k, hv, av]) => (
            <tr key={k} className="border-t border-line/60">
              <td className="py-1 font-mono text-riv">{hv ?? "–"}</td>
              <td className="py-1 text-center text-slate-400">{k}</td>
              <td className="py-1 text-right font-mono text-nor">{av ?? "–"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
