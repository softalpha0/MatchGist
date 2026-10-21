"use client";

import { useState } from "react";
import { addFan } from "@/lib/api";
import type { Channel, Fan, Language } from "@/lib/types";

const LANGS: [Language, string][] = [
  ["en", "English"],
  ["hi", "Hindi"],
  ["id", "Bahasa Indonesia"],
  ["pt-BR", "Português (BR)"],
  ["ar", "Arabic"],
  ["pcm", "Nigerian Pidgin"],
];
const CHANNELS: Channel[] = ["sms", "chat", "voice", "watch", "push"];

export function AddFan({ matchId, onClose }: { matchId: string; onClose: () => void }) {
  const [name, setName] = useState("Fan on a bus");
  const [language, setLanguage] = useState<Language>("pt-BR");
  const [channel, setChannel] = useState<Channel>("sms");
  const [budget, setBudget] = useState("50");
  const [pings, setPings] = useState("3");
  const [club, setClub] = useState("");
  const [onlyMine, setOnlyMine] = useState(false);
  const [mode, setMode] = useState<"casual" | "analyst">("casual");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    const fan: Fan = {
      fan_id: `fan_${Date.now().toString(36)}`,
      display_name: name.trim() || "New fan",
      language,
      mode: club ? (mode === "analyst" ? "analyst" : "club_focus") : mode,
      favorite_club: club || null,
      favorite_player: null,
      focus_metric: null,
      channel,
      data_budget_kb: budget ? Number(budget) : null,
      max_pings: pings ? Number(pings) : null,
      only_if_involved: Boolean(club) && onlyMine,
      quiet_after_minute: null,
    };
    try {
      await addFan(matchId, fan);
      onClose();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }

  const field = "w-full rounded-md border border-line bg-panel-2 px-2 py-1.5 text-sm";
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose}>
      <form onSubmit={submit} onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md space-y-3 rounded-2xl border border-line bg-panel p-5 shadow-2xl">
        <div className="text-lg font-semibold">Add a fan</div>
        <p className="text-xs text-slate-400">They join from the current minute with a fresh budget. Watch the Budget Guard plan around it.</p>
        <label className="block text-xs text-slate-400">Name
          <input className={field} value={name} onChange={(e) => setName(e.target.value)} maxLength={40} />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-xs text-slate-400">Language
            <select className={field} value={language} onChange={(e) => setLanguage(e.target.value as Language)}>
              {LANGS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </label>
          <label className="block text-xs text-slate-400">Channel
            <select className={field} value={channel} onChange={(e) => setChannel(e.target.value as Channel)}>
              {CHANNELS.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </label>
          <label className="block text-xs text-slate-400">Data budget (KB, empty = unlimited)
            <input className={field} value={budget} onChange={(e) => setBudget(e.target.value.replace(/[^\d.]/g, ""))} />
          </label>
          <label className="block text-xs text-slate-400">Ping limit (empty = unlimited)
            <input className={field} value={pings} onChange={(e) => setPings(e.target.value.replace(/\D/g, ""))} />
          </label>
          <label className="block text-xs text-slate-400">Depth
            <select className={field} value={mode} onChange={(e) => setMode(e.target.value as "casual" | "analyst")}>
              <option value="casual">casual</option>
              <option value="analyst">analyst</option>
            </select>
          </label>
          <label className="block text-xs text-slate-400">Favourite club
            <select className={field} value={club} onChange={(e) => setClub(e.target.value)}>
              <option value="">none</option>
              <option value="RIV">Riverside Athletic</option>
              <option value="NOR">Northgate Rovers</option>
            </select>
          </label>
        </div>
        {club && (
          <label className="flex items-center gap-2 text-xs text-slate-300">
            <input type="checkbox" checked={onlyMine} onChange={(e) => setOnlyMine(e.target.checked)} />
            Only tell me about my club
          </label>
        )}
        {error && <div className="text-xs text-red-400">{error}</div>}
        <div className="flex justify-end gap-2 pt-1">
          <button type="button" onClick={onClose} className="rounded-md px-3 py-1.5 text-sm text-slate-300 hover:bg-panel-2">Cancel</button>
          <button disabled={busy} className="rounded-md bg-accent px-3 py-1.5 text-sm font-semibold text-ink disabled:opacity-50">
            {busy ? "Adding…" : "Add fan"}
          </button>
        </div>
      </form>
    </div>
  );
}
