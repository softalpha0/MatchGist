# Overlay cue format

Touchline's output is a stream of **overlay cues**: timed, machine-readable instructions a broadcast
graphics engine (or any web or OTT player) can render on top of the live feed. The live JSON Schema
is served at `/api/schema/cue`.

## Example

```json
{
  "id": "c-m7-i42",
  "insight_id": "m7-i42",
  "kind": "goal",
  "revision": 1,
  "t_in": 4012.5,
  "t_out": 4037.5,
  "slot": "full_panel",
  "priority": 90,
  "anchor": { "player_id": "hcf-9", "side": "home", "x": 88.1, "y": 30.4 },
  "headline": "Your club: GOAL — Ade Varga 67'",
  "why": "A 6% chance: roughly 1 in 17 shots from there go in. It came against the run of play: Redmarsh Town had been the stronger side.",
  "chips": [{ "label": "xG", "value": 0.06, "unit": "" }],
  "lang": "en",
  "source": "agents"
}
```

## Fields

| Field | Meaning |
|---|---|
| `t_in`, `t_out` | Match-clock seconds (continuous across halves) between which the graphic should be on air |
| `slot` | Screen region: `full_panel`, `lower_third`, `corner_bug`, `player_tag`, `pitch_arrow`, `ticker` |
| `priority` | 0–100. Exclusive slots (`full_panel`, `lower_third`, `corner_bug`) show one cue at a time. A higher priority pre-empts; goals and period ends always air. |
| `anchor` | What the graphic attaches to: `player_id` for tags (follow the player's tracking position), `side`, and pitch coordinates (`x`, `y`, `end_x`, `end_y`) for arrows |
| `headline` | Short on-screen title, already localised and personalised |
| `chips` | Stat chips (`label`, `value`, `unit`, optional `pinned` for the viewer's chosen metric) |
| `why` | The agents' explanation of why the moment matters. Absent in revision 0. |
| `revision` | `0` is the instant deterministic cue from the Director. `1` adds the agents' `why`. Engines update the cue on air in place. |
| `source` | `director` or `agents` |

## Delivery

`GET ws://<host>/ws/match?seed=<int>&speed=<x>&profile=<json>` streams:

| `type` | Payload |
|---|---|
| `hello` | Match metadata, rosters, model backend |
| `frame` | Tracking snapshot (all players and the ball), clock, score, possession (10 per second) |
| `events` | Notable raw events |
| `cue` | An `OverlayCue` (new or revised) |
| `stats` | Shared-state snapshot: team stats, momentum, control vs chaos, rhythm, pressing, per-player physical and technical numbers |
| `traces` | Agent Ops: each agent decision (ok, skipped, rejected, timeout, error, breaker_open, repaired, quarantined) |
| `end` | Final state |

Client commands (send as JSON text): `{"type":"profile","profile":{…}}`, `{"type":"speed","speed":16}`,
`{"type":"pause","paused":true}`, `{"type":"chaos","fault":"model_outage|slow_model|hallucination|duplicate|reorder|corrupt|ghost|malformed"}`.

## Latency

Revision 0 cues are produced in the same tick as the event (around 2 ms of processing per tick). The
`why` arrives when the enrichment workflow finishes: immediately on the offline backend, and typically
1–3 s on Foundry, bounded by `TOUCHLINE_LLM_TIMEOUT`. After that the template explanation is used.
