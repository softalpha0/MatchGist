"use client";

// Original device mock-ups (not modelled on any real phone, watch or app UI).
import { useEffect, useRef } from "react";
import { audioUrl } from "@/lib/api";
import type { Delivery, Fan, LedgerSummary } from "@/lib/types";
import { WhyButton } from "./Evidence";

const LANG_LABEL: Record<string, string> = {
  en: "English",
  hi: "Hindi",
  id: "Bahasa",
  "pt-BR": "Português",
  ar: "Arabic",
  pcm: "Pidgin",
};
const CHANNEL_LABEL: Record<string, string> = {
  sms: "SMS",
  chat: "Chat",
  voice: "Voice note",
  watch: "Watch",
  push: "Push",
  broadcast: "Overlay",
};
const isRtl = (lang: string) => lang === "ar";

export function BudgetMeters({ fan, ledger }: { fan: Fan; ledger?: LedgerSummary }) {
  const used = ledger?.data_used_kb ?? 0;
  const budget = fan.data_budget_kb;
  const pct = budget ? Math.min(100, (used / budget) * 100) : 0;
  const pingsLeft = ledger?.pings_left ?? fan.max_pings;
  const binding = ledger?.binding ?? "none";
  return (
    <div className="space-y-1.5 text-[11px]">
      <div className="flex items-center justify-between text-slate-400">
        <span>Data</span>
        <span className="font-mono text-slate-200">
          {used.toFixed(1)} KB{budget ? ` / ${budget >= 1024 ? `${(budget / 1024).toFixed(1)} MB` : `${budget} KB`}` : " · unlimited"}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-slate-800">
        <div
          className={`h-1.5 rounded-full ${binding === "data" ? "bg-amber-400" : "bg-accent-2"}`}
          style={{ width: `${Math.max(pct, budget ? 1.5 : 0)}%` }}
        />
      </div>
      <div className="flex items-center justify-between text-slate-400">
        <span>Pings</span>
        {fan.max_pings ? (
          <span className="flex gap-1">
            {Array.from({ length: fan.max_pings }).map((_, i) => (
              <span
                key={i}
                className={`h-2 w-2 rounded-full ${i < (pingsLeft ?? 0) ? (binding === "pings" ? "bg-amber-400" : "bg-accent") : "bg-slate-700"}`}
              />
            ))}
          </span>
        ) : (
          <span className="font-mono text-slate-200">unlimited</span>
        )}
      </div>
      <div className="flex items-center justify-between">
        <span className="text-slate-400">Binding limit</span>
        <span
          className={`rounded px-1.5 py-0.5 font-medium ${
            binding === "pings" ? "bg-amber-400/15 text-amber-300" : binding === "data" ? "bg-amber-400/15 text-amber-300" : "bg-slate-700/60 text-slate-300"
          }`}
        >
          {binding === "none" ? "none" : binding}
        </span>
      </div>
    </div>
  );
}

function Shell({ fan, ledger, children, accent }: { fan: Fan; ledger?: LedgerSummary; children: React.ReactNode; accent: string }) {
  return (
    <div className="flex h-full min-h-0 flex-col rounded-2xl border border-line bg-panel p-3 shadow-lg">
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-slate-100">{fan.display_name}</div>
          <div className="text-[11px] text-slate-400">
            {LANG_LABEL[fan.language] ?? fan.language} · {fan.mode.replace("_", " ")}
            {fan.favorite_club ? ` · ${fan.favorite_club}` : ""}
            {fan.only_if_involved ? " only" : ""}
          </div>
        </div>
        <span className={`shrink-0 rounded-md px-2 py-0.5 text-[11px] font-semibold ${accent}`}>{CHANNEL_LABEL[fan.channel]}</span>
      </div>
      <div className="min-h-0 flex-1">{children}</div>
      <div className="mt-2 border-t border-line pt-2">
        <BudgetMeters fan={fan} ledger={ledger} />
      </div>
    </div>
  );
}

function Empty({ text = "Waiting for a moment worth the budget…" }: { text?: string }) {
  return <div className="flex h-full items-center justify-center px-4 text-center text-xs text-slate-500">{text}</div>;
}

function Meta({ d }: { d: Delivery }) {
  return (
    <div className="mt-1 flex flex-wrap gap-x-2 text-[10px] text-slate-500">
      <span>{d.match_clock}</span>
      {d.segments != null && (
        <span>
          {d.segments} seg · {d.encoding}
        </span>
      )}
      <span>{d.size_kb} KB</span>
      {d.kind === "bundle" && <span className="text-accent-2">bundled</span>}
      {d.kind === "digest" && <span className="text-accent">digest</span>}
      {d.fallback_used && <span className="text-amber-400">template</span>}
      <WhyButton d={d} />
    </div>
  );
}

function Phone({ children, title, count, newestFirst = false }: {
  children: React.ReactNode;
  title: string;
  count: number;
  newestFirst?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    // keep the newest message in view, like a real inbox
    const el = ref.current;
    if (el) el.scrollTo({ top: newestFirst ? 0 : el.scrollHeight, behavior: "smooth" });
  }, [count, newestFirst]);
  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-[20px] border-[3px] border-slate-700 bg-[#0e141c]">
      <div className="flex items-center justify-between bg-[#151d28] px-3 py-1.5 text-[10px] text-slate-400">
        <span>{title}</span>
        <span className="flex items-center gap-1">
          <span className="h-1.5 w-3 rounded-sm bg-slate-500" />
          <span className="h-1.5 w-1.5 rounded-full bg-slate-500" />
        </span>
      </div>
      <div ref={ref} className="scrollbar-thin flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto p-2">{children}</div>
    </div>
  );
}

export function SmsDevice({ fan, ledger, deliveries }: { fan: Fan; ledger?: LedgerSummary; deliveries: Delivery[] }) {
  return (
    <Shell fan={fan} ledger={ledger} accent="bg-emerald-400/15 text-emerald-300">
      <Phone title="Messages · MatchGist" count={deliveries.length}>
        {deliveries.length === 0 && <Empty />}
        {deliveries.map((d) => (
          <div key={d.delivery_id} className="animate-pop max-w-[92%] self-start">
            <div
              dir={isRtl(d.language) ? "rtl" : "ltr"}
              className={`rounded-2xl rounded-bl-md px-3 py-2 text-[13px] leading-snug ${d.kind === "digest" ? "bg-emerald-900/60 ring-1 ring-emerald-500/40" : "bg-slate-700/70"}`}
            >
              {d.text}
            </div>
            <Meta d={d} />
          </div>
        ))}
      </Phone>
    </Shell>
  );
}

export function ChatDevice({ fan, ledger, deliveries }: { fan: Fan; ledger?: LedgerSummary; deliveries: Delivery[] }) {
  return (
    <Shell fan={fan} ledger={ledger} accent="bg-sky-400/15 text-sky-300">
      <Phone title="Chat · MatchGist bot" count={deliveries.length}>
        {deliveries.length === 0 && <Empty />}
        {deliveries.map((d) => (
          <div key={d.delivery_id} className="animate-pop max-w-[92%] self-start">
            <div dir={isRtl(d.language) ? "rtl" : "ltr"} className="rounded-xl bg-sky-950/70 px-3 py-2 text-[13px] ring-1 ring-sky-800/60">
              {d.text}
            </div>
            <Meta d={d} />
          </div>
        ))}
      </Phone>
    </Shell>
  );
}

export function VoiceDevice({ fan, ledger, deliveries }: { fan: Fan; ledger?: LedgerSummary; deliveries: Delivery[] }) {
  return (
    <Shell fan={fan} ledger={ledger} accent="bg-violet-400/15 text-violet-300">
      <Phone title="Voice notes" count={deliveries.length}>
        {deliveries.length === 0 && <Empty />}
        {deliveries.map((d) => (
          <div key={d.delivery_id} className="animate-pop rounded-xl bg-violet-950/50 p-2 ring-1 ring-violet-800/50">
            <div className="flex items-center gap-2">
              {d.audio_url ? (
                <audio controls src={audioUrl(d.audio_url)} className="h-7 w-full" />
              ) : (
                <>
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-violet-500 text-xs">▶</span>
                  <span className="flex h-6 flex-1 items-center gap-[2px]">
                    {Array.from({ length: 22 }).map((_, i) => (
                      <span
                        key={i}
                        className="wave-bar w-[3px] rounded bg-violet-300/70"
                        style={{ height: `${30 + ((i * 37) % 70)}%`, animationDelay: `${(i % 7) * 0.12}s` }}
                      />
                    ))}
                  </span>
                </>
              )}
              <span className="shrink-0 font-mono text-[11px] text-violet-200">{d.audio_seconds?.toFixed(1)}s</span>
            </div>
            <div className="mt-1.5 text-[12px] text-slate-300">“{d.text}”</div>
            <div className="mt-1 text-[10px] text-slate-500">
              {d.audio_url ? d.voice : `transcript only (speech not configured) · ${d.voice ?? ""}`}
            </div>
            <Meta d={d} />
          </div>
        ))}
      </Phone>
    </Shell>
  );
}

export function PushDevice({ fan, ledger, deliveries }: { fan: Fan; ledger?: LedgerSummary; deliveries: Delivery[] }) {
  return (
    <Shell fan={fan} ledger={ledger} accent="bg-orange-400/15 text-orange-300">
      <Phone title="Lock screen" count={deliveries.length} newestFirst>
        {deliveries.length === 0 && <Empty />}
        {[...deliveries].reverse().map((d) => (
          <div key={d.delivery_id} className="animate-pop rounded-xl bg-slate-800/80 p-2 ring-1 ring-slate-600/40 backdrop-blur">
            <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
              <span className="h-3 w-3 rounded bg-accent" /> MATCHGIST · {d.match_clock}
            </div>
            <div dir={isRtl(d.language) ? "rtl" : "ltr"} className="mt-0.5 text-[13px] font-semibold">
              {d.title}
            </div>
            <div dir={isRtl(d.language) ? "rtl" : "ltr"} className="text-[12px] text-slate-300">
              {d.text}
            </div>
            <Meta d={d} />
          </div>
        ))}
      </Phone>
    </Shell>
  );
}

export function WatchDevice({ fan, ledger, deliveries }: { fan: Fan; ledger?: LedgerSummary; deliveries: Delivery[] }) {
  const last = deliveries[deliveries.length - 1];
  return (
    <Shell fan={fan} ledger={ledger} accent="bg-pink-400/15 text-pink-300">
      <div className="flex h-full flex-col items-center justify-center gap-2">
        <div className="relative flex h-36 w-36 items-center justify-center rounded-full border-[6px] border-slate-700 bg-black shadow-inner">
          <div className="absolute -right-2 top-1/2 h-6 w-2 -translate-y-1/2 rounded bg-slate-700" />
          {last ? (
            <div key={last.delivery_id} className="animate-pop px-3 text-center" dir={isRtl(last.language) ? "rtl" : "ltr"}>
              <div className="text-[11px] leading-tight text-slate-300">{last.text}</div>
              {last.value && <div className="mt-1 font-mono text-2xl font-bold text-accent">{last.value}</div>}
              <div className="mt-1 text-[9px] text-slate-500">{last.match_clock}</div>
              <div className="text-[9px]"><WhyButton d={last} /></div>
            </div>
          ) : (
            <div className="text-[10px] text-slate-500">idle</div>
          )}
        </div>
        <div className="text-[10px] text-slate-500">
          {deliveries.length} glance{deliveries.length === 1 ? "" : "s"}
          {last ? ` · last ${last.size_kb} KB` : ""}
        </div>
      </div>
    </Shell>
  );
}

export function Device({ fan, ledger, deliveries }: { fan: Fan; ledger?: LedgerSummary; deliveries: Delivery[] }) {
  switch (fan.channel) {
    case "sms":
      return <SmsDevice fan={fan} ledger={ledger} deliveries={deliveries} />;
    case "chat":
      return <ChatDevice fan={fan} ledger={ledger} deliveries={deliveries} />;
    case "voice":
      return <VoiceDevice fan={fan} ledger={ledger} deliveries={deliveries} />;
    case "push":
      return <PushDevice fan={fan} ledger={ledger} deliveries={deliveries} />;
    case "watch":
      return <WatchDevice fan={fan} ledger={ledger} deliveries={deliveries} />;
    default:
      return null;
  }
}
