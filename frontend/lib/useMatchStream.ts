"use client";

import { useEffect, useReducer, useRef } from "react";
import { streamUrl } from "./api";
import type { AgentEvent, Delivery, Fan, LedgerSummary, MatchEvent, Moment, Snapshot } from "./types";

export interface StreamState {
  connected: boolean;
  ended: boolean;
  snapshot: Snapshot | null;
  fans: Fan[];
  ledgers: Record<string, LedgerSummary>;
  deliveries: Record<string, Delivery[]>; // by fan
  events: MatchEvent[]; // recent, for the pitch
  eventIndex: Map<string, MatchEvent>; // every event so far, for the evidence drawer
  names: Record<string, string>; // player id -> name
  moments: Moment[];
  agentEvents: AgentEvent[];
  error: string | null;
}

function fresh(): StreamState {
  return {
    connected: false,
    ended: false,
    snapshot: null,
    fans: [],
    ledgers: {},
    deliveries: {},
    events: [],
    eventIndex: new Map(),
    names: {},
    moments: [],
    agentEvents: [],
    error: null,
  };
}

type Action =
  | { t: "reset" }
  | { t: "open" }
  | { t: "error"; msg: string }
  | { t: "snapshot"; d: Snapshot & { names?: Record<string, string> } }
  | { t: "event"; d: MatchEvent }
  | { t: "moment"; d: Moment }
  | { t: "delivery"; d: Delivery }
  | { t: "agent_event"; d: AgentEvent }
  | { t: "fan_joined"; d: { fan: Fan; ledger: LedgerSummary } }
  | { t: "end"; d: { ledgers: Record<string, LedgerSummary> } };

const MAX_EVENTS = 40;
const MAX_AGENT_EVENTS = 600;

function reduce(s: StreamState, a: Action): StreamState {
  switch (a.t) {
    case "reset":
      return fresh();
    case "open":
      return { ...s, connected: true, error: null };
    case "error":
      return { ...s, connected: false, error: a.msg };
    case "snapshot":
      return {
        ...s,
        snapshot: a.d,
        fans: a.d.fans ?? s.fans,
        ledgers: a.d.ledgers ?? s.ledgers,
        names: a.d.names ?? s.names,
      };
    case "event":
      // the index is append-only and owned by this state, so it is updated in place (1,000+ events)
      s.eventIndex.set(a.d.event_id, a.d);
      return { ...s, events: [...s.events.slice(-MAX_EVENTS + 1), a.d] };
    case "moment":
      return s.moments.some((m) => m.moment_id === a.d.moment_id) ? s : { ...s, moments: [...s.moments, a.d] };
    case "delivery": {
      const list = s.deliveries[a.d.fan_id] ?? [];
      if (list.some((d) => d.delivery_id === a.d.delivery_id)) return s;
      const ledger = s.ledgers[a.d.fan_id];
      return {
        ...s,
        deliveries: { ...s.deliveries, [a.d.fan_id]: [...list, a.d] },
        ledgers: ledger
          ? { ...s.ledgers, [a.d.fan_id]: { ...ledger, ...a.d.budget_after, deliveries: list.length + 1 } }
          : s.ledgers,
      };
    }
    case "agent_event":
      return { ...s, agentEvents: [...s.agentEvents.slice(-MAX_AGENT_EVENTS + 1), a.d] };
    case "fan_joined":
      return s.fans.some((f) => f.fan_id === a.d.fan.fan_id)
        ? s
        : { ...s, fans: [...s.fans, a.d.fan], ledgers: { ...s.ledgers, [a.d.fan.fan_id]: a.d.ledger } };
    case "end":
      return { ...s, ended: true, ledgers: { ...s.ledgers, ...a.d.ledgers } };
  }
}

const NAMES = ["snapshot", "stats", "event", "moment", "delivery", "agent_event", "fan_joined", "end"] as const;

function toAction(name: string, d: unknown): Action {
  return (name === "stats" || name === "snapshot" ? { t: "snapshot", d } : { t: name, d }) as Action;
}

/** Live: a match on the API server. Replay: a recorded match served as a static file (no server needed). */
export type Source =
  | { kind: "live"; matchId: string }
  | { kind: "replay"; storyline: string; run: number }
  | null;

type Recorded = [number, string, unknown];

export interface ReplayMeta {
  storyline: string;
  model: string;
  recorded_at: string;
  final_score: [number, number];
  home: string;
  away: string;
}

export interface Feed {
  state: StreamState;
  /** Replay only: play forward to the first event that matches (instantly). */
  jump: ((match: (e: MatchEvent) => boolean) => void) | null;
  meta: ReplayMeta | null;
}

/** Fold a live SSE stream, or a recorded replay played at ``speed``x, into one state object. */
export function useMatchFeed(source: Source, speed: number): Feed {
  const [state, dispatch] = useReducer(reduce, undefined, fresh);
  const speedRef = useRef(speed);
  speedRef.current = speed;
  const jumpRef = useRef<Feed["jump"]>(null);
  const metaRef = useRef<ReplayMeta | null>(null);
  const key = source ? (source.kind === "live" ? `live:${source.matchId}` : `replay:${source.storyline}:${source.run}`) : "";

  useEffect(() => {
    dispatch({ t: "reset" });
    jumpRef.current = null;
    metaRef.current = null;
    if (!source) return;

    if (source.kind === "live") {
      const es = new EventSource(streamUrl(source.matchId));
      es.onopen = () => dispatch({ t: "open" });
      es.onerror = () => {
        // the server closes the stream after "end"; anything else is a real disconnect
        dispatch({ t: "error", msg: "stream closed" });
        es.close();
      };
      for (const name of NAMES) {
        es.addEventListener(name, (e) => dispatch(toAction(name, JSON.parse((e as MessageEvent).data))));
      }
      return () => es.close();
    }

    let cancelled = false;
    let timer: ReturnType<typeof setInterval> | undefined;
    let msgs: Recorded[] = [];
    let i = 0;
    let t = 0;
    const flush = () => {
      while (i < msgs.length && msgs[i][0] <= t) {
        const [, name, d] = msgs[i++];
        dispatch(toAction(name, d));
      }
      if (i >= msgs.length && timer) clearInterval(timer);
    };
    fetch(`/replays/${source.storyline}.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`replay ${source.storyline}: ${r.status}`);
        return r.json() as Promise<{ meta: ReplayMeta; messages: Recorded[] }>;
      })
      .then((doc) => {
        if (cancelled) return;
        msgs = doc.messages;
        metaRef.current = doc.meta;
        dispatch({ t: "open" });
        jumpRef.current = (match) => {
          const k = msgs.findIndex((m, j) => j >= i && m[1] === "event" && match(m[2] as MatchEvent));
          if (k >= 0) {
            t = Math.max(t, msgs[k][0]);
            flush();
          }
        };
        let last = performance.now();
        timer = setInterval(() => {
          const now = performance.now();
          t += ((now - last) / 1000) * speedRef.current;
          last = now;
          flush();
        }, 100);
        flush();
      })
      .catch((e) => !cancelled && dispatch({ t: "error", msg: String(e) }));
    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
    // the source object is recreated by callers; its identity is captured by `key`
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return { state, jump: jumpRef.current, meta: metaRef.current };
}
