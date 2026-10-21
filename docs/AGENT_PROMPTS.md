# Claude Code prompts — MatchGist

## Before you start (one time)

Run these in PowerShell:

```powershell
mkdir matchgist; cd matchgist
git init
mkdir docs
# copy CLAUDE.md, HACKATHON_BRIEF.md and SPEC.md into this folder now
git add .; git commit -m "docs: project brief, spec and agent guide"
gh repo create matchgist --public --source . --push   # or create it on github.com and push
claude
```

Claude Code reads `CLAUDE.md` automatically every session. The prompts below assume the three docs are in the repo root.

---

## Prompt 1 — Kickoff (Milestone M1)

Paste this as your first message in Claude Code:

```
Read CLAUDE.md, HACKATHON_BRIEF.md and SPEC.md fully before doing anything.

Then give me:
1. A 5-line summary of what MatchGist is, what makes it different from the other entries, and the hard rules you must follow.
2. Any gaps or contradictions you see between the brief and the spec.
3. A step-by-step plan for Milestone M1 only (SPEC §15).

Wait for my OK before writing code.

M1 scope:
- Scaffold the repo exactly as in SPEC §12. Future modules get a one-line docstring saying what goes there.
- backend/pyproject.toml: Python 3.11+, fastapi, uvicorn, pydantic v2, pytest, ruff. No agent or Azure packages yet (M3/M4).
- .env.example with the keys in SPEC §11.1 (empty values); .gitignore excluding .env, .venv, __pycache__, node_modules, matches/*.jsonl.
- data/clubs.json: Riverside Athletic (RIV) and Northgate Rovers (NOR), 16 players each per SPEC §8.1. Varied names from many countries. Nothing that matches a real player or club.
- data/fans.json: the 6 demo personas in SPEC §5.1, using the profile schema in SPEC §5.
- Pydantic models in backend/app/simulator/schema.py for every event type in SPEC §8.2, and in backend/app/fans/profiles.py for the fan profile. Document both in docs/event-schema.md.
- Simulator in backend/app/simulator/engine.py per SPEC §8.3:
  - seeded and fully deterministic (same seed = identical output)
  - possession-chain model; player ratings affect pass success, shot speed and xG
  - kickoff, two halves, half_time, full_time; 1,200-1,800 events; realistic score
  - valid coordinates (x 0-105, y 0-68); seq and match_clock always increase
  - storylines in storylines.py: none, comeback, red_card, late_drama
  - CLI: python -m app.simulator --seed 42 --storyline comeback --out ../matches/m001.jsonl
  - stream_events(match, speed) generator yielding events in real time scaled by speed (1, 10, 60)
- backend/app/main.py: GET /health; POST /matches returning match_id and event count; GET /fans listing personas.
- Tests: determinism; every event validates; event count in range; clock and seq increase; comeback (trailing team at 70' finishes level or ahead); late_drama (a goal after 85'); fans.json validates.
- .github/workflows/ci.yml running ruff and pytest on push.
- README.md placeholder: name, the pitch from SPEC §1 in two lines, PowerShell setup/run/test commands.
- docs/PROGRESS.md: milestone checklist from SPEC §15, current status, open decisions.

Rules while building:
- All commands must work in Windows PowerShell.
- Run ruff and pytest after each step; fix failures before moving on.
- Commit after each logical step with Conventional Commit messages.

When M1 is done, give me:
1. Exact PowerShell commands to create the venv, install, run tests, generate a match and start the API.
2. A summary of one generated match: final score, event count, top 3 passers, and when the goals came.
3. Anything I need to decide before M2.

Don't start M2 until I confirm.
```

---

## Prompt 2 — Every later milestone

Use this for M2 to M7. Change only the milestone number, and add the matching line from the table below.

```
Read docs/PROGRESS.md, then re-read the parts of SPEC.md and HACKATHON_BRIEF.md that apply to Milestone M2.

Give me a short plan for M2 (SPEC §15) and wait for my OK.

When done: update docs/PROGRESS.md, run ruff and pytest, commit, and give me the PowerShell commands to run and check it, plus anything uncertain.
```

### Extra line per milestone

| Milestone | Add this |
|---|---|
| M2 | `Build channels/limits.py, sms_encoding.py and sizing.py per SPEC §6 first, with thorough tests: pure GSM-7 text, text with one non-GSM character, Hindi, Arabic, emoji, exactly 160/161 and 70/71 characters, and multi-segment messages (153 and 67 chars per segment when concatenated). Then the Stats Engine, Moment Detector and the SSE stream.` |
| M3 | `Check the current Microsoft Agent Framework and Foundry docs before writing integration code, and pin package versions. Use gpt-4o-mini. Build the Verifier, fallback templates and the Budget Guard (pure code) first, with tests, then the LLM agents. Run one full match at speed 60 with all 6 personas and show me every delivery per persona, plus each Budget Guard decision and reason.` |
| M4 | `Check the current Azure AI Speech docs and tell me which demo languages have neural voices before writing code. For any language without a voice, the voice channel falls back to text and says so. Show me the actual duration and size of three generated voice notes.` |
| M5 | `Before building, describe the screen layout from SPEC §14 in words and wait for my OK. It must look clean in a 1080p screen recording. Device mock-ups must be original designs, not copies of any real phone, app or brand UI.` |
| M6 | `Give me the exact az CLI commands to deploy to Azure Container Apps on the consumption plan and to set a $50 budget alert. Don't run anything that costs money without asking. Then write the full README per SPEC §17 and docs/architecture.md with a Mermaid diagram.` |
| M7 | `Run the submission checklist in SPEC §18 and HACKATHON_BRIEF.md §4. Search the whole repo for any real club, player or league names. Check the live URL works in a private window with no login.` |

---

## Handy one-liners

| Situation | Prompt |
|---|---|
| Something broke | `Run the tests, read the failure, find the root cause and fix it. Don't change tests to make them pass unless the test is wrong; tell me if so.` |
| Session getting long | `Update docs/PROGRESS.md with everything done and pending, then commit.` |
| Before recording | `Run seed 42, storyline late_drama, speed 60, and list minute by minute what each of the 6 personas receives, with data used and pings left.` |
| Drift check | `Compare what's built against HACKATHON_BRIEF.md §2, §5 and §9. List what's missing that would cost us points, ordered by impact.` |
| Cost check | `Estimate the Foundry and Speech cost of one full demo match with 6 personas. Show the calculation.` |
