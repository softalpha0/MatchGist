# Hackathon brief: the rules we build to

Source: the organisers' public repo (github.com/microsoft/insidethegamehackathon: `OFFICIAL RULES.md`) and the
event page at https://aka.ms/insidethegame. The Official Rules win if anything here differs.
A longer working copy is in `HACKATHON_BRIEF.md`.

## Deadline

- Submission period ends **Oct 27, 2026, 11:59 PM Pacific Time** (Wed Oct 28, 7:59 AM WAT).
- Our internal target: **Tue Oct 27, 11:00 PM WAT**.
- Judging Oct 27 to Nov 10; winners by Nov 20. The project must stay testable, free and unrestricted, until
  judging ends.

## Submission requirements

| # | Item | Our answer |
|---|---|---|
| 1 | Project description: what it does, which Microsoft and Azure tech, the problem it solves | `docs/submission.md` |
| 2 | Demo video under 2 minutes, public on YouTube, Vimeo, Facebook Video or Youku, no copyrighted music | to record |
| 3 | Public GitHub repo URL | github.com/softalpha0/MatchGist (to push) |
| 4 | Testing access: a working link, free, no restrictions until judging ends | Netlify site (no login) |

Other rules that shape the build: synthetic, football-realistic data only (no data is provided by the
organisers, so we generate our own); no third-party trademarks, real clubs, players or crests; new and original
work; must run as shown; English submission materials.

## Judging

**Stage 1 (pass/fail):** fits the theme and reasonably uses the required technologies.

**Stage 2 (20% each):** technological implementation; agentic design and innovation; real-world impact;
user experience and presentation; category fit. Ties are broken in that order.

Hero technologies named by the organisers: Microsoft Foundry, Microsoft Agent Framework, Azure MCP, GitHub
Copilot Agent Mode, Microsoft Fabric, GitHub SDK, GitHub CLI, Azure Apps and AI Services, Azure databases.

Our category: **Best Multi-Agent System** (agents with distinct roles, shared state and handoffs, recovery
from failures, an end-to-end result one agent couldn't reach).

## Required pipeline

| Stage | Where MatchGist does it |
|---|---|
| Ingest synthetic events as they happen | `backend/app/simulator/`, streamed by `runtime.py` |
| Interpret into stats, patterns, context | `backend/app/stats/`, `backend/app/moments/` |
| Explain why a moment matters | Explainer agent, `backend/app/agents/explainer.py` |
| Render timed, machine-readable output for overlays | overlay cues, `backend/app/channels/adapters.py` |
| Personalize for analyst vs casual fan, club, player, language | Ranker, Budget Guard, Localizer, Compressor |
