# CLAUDE.md — MatchGist

Claude Code loads this file automatically. Keep it short; details live in the docs below.

## What this repo is

MatchGist: a multi-agent system that turns a live stream of **synthetic** football events into explained match intelligence, then fits it to each fan's channel (SMS, chat, voice note, watch, push, broadcast overlay), data budget, ping limit, language, and depth. Entry for Microsoft's "Inside the Game" Developer Hackathon.

## Read these first

| File | What it holds |
|---|---|
| `HACKATHON_BRIEF.md` | Rules, required pipeline, judging, prize categories, submission requirements, competitor landscape |
| `SPEC.md` | Fan profile, channel limits and size model, architecture, agents, schema, stats, API, UI, milestones |
| `docs/PROGRESS.md` | What's done, what's next, open decisions. **Update it at the end of every session** |

If `SPEC.md` and `HACKATHON_BRIEF.md` conflict, the brief (the rules) wins. Flag the conflict to me.

## Non-negotiables

1. **Fictional data only.** No real club names, player names, crests, or league branding anywhere: code, tests, comments, seed data, UI, screenshots. Fan personas are fictional too.
2. **LLMs never invent numbers.** All stats come from the Stats Engine. The Verifier checks that every number in an output exists in the Match State snapshot.
3. **Channel limits are hard limits.** The Verifier enforces them in code. SMS length is measured in segments with real GSM-7 vs UCS-2 detection (160 vs 70 chars), never by `len()`.
4. **The feed never stops.** Every agent call has a timeout, retries, and a per-channel, per-language template fallback. Log fallbacks and Budget Guard decisions as `agent_events`.
5. **Deadline:** submit by Tue Oct 27, 11:00 PM WAT. Prefer simple, working code over clever abstractions.
6. **Budget:** $200 Azure credit. Default model `gpt-4o-mini`. Never create paid Azure resources or add paid services without asking me.
7. **Secrets:** never commit `.env` or keys. Only `.env.example` with empty values.

## Environment

- Windows + **PowerShell**. Commands must work in PowerShell: use `;` not `&&`, `$env:VAR = "x"`, `.\.venv\Scripts\Activate.ps1`.
- Python 3.11+ backend (FastAPI), TypeScript frontend (Next.js + Tailwind).
- Agents: Microsoft Agent Framework (Python), models from Microsoft Foundry. Voice: Azure AI Speech.
- Hosting: Azure Container Apps (consumption plan).

## Conventions

- Backend in `backend/app/`, tests in `backend/tests/`, frontend in `frontend/`.
- Pydantic v2 models for every event, fan profile, delivery, and API payload.
- `ruff` for lint and format; `pytest` for tests. Run both before every commit.
- Small commits with Conventional Commit messages (`feat(sim): ...`, `fix(channels): ...`, `test: ...`, `docs: ...`).
- Docstrings on public functions. Comments explain *why*, not *what*.
- Microsoft libraries (Agent Framework, Foundry, Speech, Communication Services) change fast. **Check the current official docs before writing integration code; don't rely on memory.** Pin versions.

## How to work with me

- Start each session by reading `docs/PROGRESS.md`.
- For each milestone, propose a short plan first and wait for my OK before writing lots of code.
- Small steps; run tests after each; fix failures before moving on.
- Stop at the end of each milestone and summarise: what was built, how to run it (PowerShell), what's uncertain.
- Ask before deleting files, rewriting large parts of working code, or changing the event schema or fan profile schema.
