"use client";

import { useEffect, useState } from "react";

interface Summary {
  true_passes: number;
  detected: number;
  recall: number;
  precision: number;
  distance_mae_m: number;
  speed_median_err_kmh: number;
  completion_accuracy: number;
}

const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

/** Auto-eventing prototype: a clip of passes detected from pixels, and how they score against the truth. */
export function VisionSection() {
  const [s, setS] = useState<Summary | null>(null);
  useEffect(() => {
    fetch("/vision/summary.json").then((r) => (r.ok ? r.json() : null)).then(setS).catch(() => setS(null));
  }, []);

  return (
    <section id="vision" className="mx-auto max-w-6xl px-6 py-20">
      <div className="text-xs uppercase tracking-wider text-accent">Prototype</div>
      <h2 className="mt-2 text-3xl font-bold tracking-tight">Auto-eventing: pass and speed metrics from video.</h2>
      <p className="mt-4 max-w-3xl text-slate-300">
        The simulator moves all 22 players and the ball every half second. We render that as a top-down camera feed,
        then a detector that sees only the pixels finds every pass, its distance and the ball&apos;s speed, and we score it
        against the simulator&apos;s ground truth. Synthetic video only: the rules allow no real footage.
      </p>
      <div className="mt-8 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <video src="/vision/clip.mp4" poster="/vision/poster.jpg" controls muted loop playsInline className="w-full rounded-xl border border-line" />
        <div className="rounded-xl border border-line bg-panel p-5">
          <div className="text-sm font-semibold">Full match, scored against the truth</div>
          {s ? (
            <table className="mt-3 w-full text-sm">
              <tbody>
                {[
                  ["Passes found", `${pct(s.recall)} of ${s.true_passes}`],
                  ["Detections that were real passes", pct(s.precision)],
                  ["Pass distance error", `${s.distance_mae_m} m (mean)`],
                  ["Ball speed error", `${s.speed_median_err_kmh} km/h (median)`],
                  ["Completed or lost, correct", pct(s.completion_accuracy)],
                ].map(([k, v]) => (
                  <tr key={k} className="border-t border-line/60">
                    <td className="py-2 pr-3 text-slate-400">{k}</td>
                    <td className="py-2 font-mono">{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="mt-3 text-sm text-slate-500">Scores load with the clip.</div>
          )}
          <p className="mt-4 text-xs text-slate-500">
            Yellow: what the detector measured. Grey: the truth. It tells teams apart by kit colour, not individual
            players, and runs offline; the live demo uses the simulator&apos;s events. Details in evidence/auto-eventing.md.
          </p>
        </div>
      </div>
      <div className="mt-6 rounded-xl border border-line bg-panel/60 p-5 text-sm text-slate-300">
        <span className="font-semibold text-white">Live speed and distance tags.</span> The same tracking drives the
        pitch in the live demo: a name tag appears when a player sprints past 30 km/h, passes 7 km covered, or when a
        shot tops 100 km/h or a pass 90 km/h.
      </div>
    </section>
  );
}
