# Submission kit

Internal deadline: **Tue 27 Oct, 11:00 PM WAT** (official: Wed 28 Oct, 7:59 AM WAT).

## Checklist

- [ ] Repo public on GitHub, README current, CI green
- [ ] Live deployment on Azure Container Apps with Foundry configured; link tested in a private window
- [ ] Demo video < 2:00, public on YouTube, no copyrighted music, only fictional clubs and players
- [ ] Pitch text pasted into Innovation Studio; category: Best Multi-Agent System
- [ ] Testing instructions: no login needed; mention `?seed=` for a reproducible match

## Pitch (draft)

**Touchline: synthetic match intelligence, explained and personalised by a team of agents.**

Broadcasters have more match data than airtime, and one feed has to serve a tactics obsessive and a
first-time fan at once. Touchline is an AI engine that ingests a live feed of synthetic football events
and tracking data, works out what matters and why, and emits timed, machine-readable overlay cues that a
graphics engine can draw over the live picture. Each viewer then gets the same intelligence told their
way: Fan or Analyst mode, their club, a player to follow all match, a pinned metric, in four languages.

It is built as a multi-agent system on **Microsoft Agent Framework**, using two workflows over a shared
match state. A deterministic live workflow (Ingest → Interpret → Director) puts graphics on screen in the
same tick as the event. An enrichment workflow, with a switch-case Dispatcher feeding Analyst →
Personalizer or a Narrator, runs on **Microsoft Foundry** and adds the "why". A Verifier rejects any
output that cites a number not present in the shared state. A Supervisor enforces timeouts, budgets and a
circuit breaker, and falls back to multilingual templates so the broadcast never stalls. Fault injection
(model outage, slow model, hallucinated stat, corrupt or duplicate or out-of-order feed) shows every
recovery live in an Agent Ops panel.

Everything runs on synthetic data from our own seeded simulator. It models team shape, pressing,
expected pass completion (which drives the pass difficulty rating), xG, ball and shot speed, sprints and
distance, and it produces realistic match volumes. It deploys as one container to **Azure Container
Apps** with managed identity, and runs for free with no keys in offline mode, so judges can always test it.

**Microsoft tech:** Microsoft Agent Framework (Agents, Workflows with chain and switch-case edges, agent
middleware), Microsoft Foundry (model deployment via `FoundryChatClient`), Azure Container Apps, Azure
Container Registry, Managed Identity, Log Analytics, Azure Developer CLI, GitHub Actions, GitHub Copilot.

## Video plan (≤ 1:55)

| Time | Shot |
|---|---|
| 0:00–0:12 | Hook: one goal, two screens: the Fan version and the Analyst version of the same moment |
| 0:12–0:30 | Problem plus what Touchline is (fictional clubs, synthetic feed) |
| 0:30–0:55 | Live view at 16×: player speed tags, pass-difficulty arrow, momentum bug, chaos index, goal panel with "why" |
| 0:55–1:15 | Personalise: switch to Spanish, pick a club, follow a player, pin xG. The graphics re-render. |
| 1:15–1:40 | Agent Ops: architecture flash, then inject "hallucinated stat" (Verifier rejects) and "model outage" (Supervisor falls back, breaker opens). The broadcast keeps going. |
| 1:40–1:55 | Cue JSON and schema, Azure + Foundry, repo link |
