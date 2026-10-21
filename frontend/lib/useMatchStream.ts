"use client";

import { useEffect, useReducer } from "react";
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
  moments: Moment[];
  agentEvents: AgentEvent[];
  error: string | null;
}

const initial: StreamState = {
  connected: false,
  ended: false,
  snapshot: null,
  fans: [],
  ledgers: {},
  deliveries: {},
  events: [],
  moments: [],
  agentEvents: [],
  error: null,
};

type Action =
  | { t: "reset" }
  | { t: "open" }
  | { t: "error"; msg: string }
  | { t: "snapshot"; d: Snapshot }
  | { t: "event"; d: MatchEvent }
  | { t: "moment"; d: Moment }
  | { t: "delivery"; d: Delivery }
  | { t: "agent_event"; d: AgentEvent }
  | { t: "fan_joined"; d: { fan: Fan; ledger: LedgerSummary } }
  | { t: "end"; d: { ledgers: Record<string, LedgerSummary> } };

const MAX_EVENTS = 40;
const MAX_AGENT_EVENTS = 400;

function reduce(s: StreamState, a: Action): StreamState {
  switch (a.t) {
    case "reset":
      return initial;
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
      };
    case "event":
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

/** Subscribe to a match's SSE stream and fold it into one state object. */
export function useMatchStream(matchId: string | null): StreamState {
  const [state, dispatch] = useReducer(reduce, initial);

  useEffect(() => {
    dispatch({ t: "reset" });
    if (!matchId) return;
    const es = new EventSource(streamUrl(matchId));
    es.onopen = () => dispatch({ t: "open" });
    es.onerror = () => {
      // the server closes the stream after "end"; anything else is a real disconnect
      dispatch({ t: "error", msg: "stream closed" });
      es.close();
    };
    for (const name of NAMES) {
      es.addEventListener(name, (e) => {
        const d = JSON.parse((e as MessageEvent).data);
        if (name === "stats" || name === "snapshot") dispatch({ t: "snapshot", d });
        else dispatch({ t: name, d } as Action);
      });
    }
    return () => es.close();
  }, [matchId]);

  return state;
}
