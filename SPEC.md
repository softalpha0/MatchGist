# MatchGist — Project Spec

> Entry for Microsoft's "Inside the Game" Developer Hackathon.
> Challenge: The Synthetic Match Insights Engine for Premier League Studio.
> Internal deadline: **Tue Oct 27, 11:00 PM WAT**. Hard deadline: Wed Oct 28, 7:59 AM WAT (Oct 27, 11:59 PM PT).

---

## 1. Pitch

Most match-intelligence tools assume a fan watching on a big screen with fast internet. Most of the world's fans aren't. They follow games on mobile data, at work, on a commute, roaming abroad, or on a basic phone.

**MatchGist** turns a live stream of synthetic football events into explained match intelligence, then fits it to what each fan actually has: their **channel** (SMS, WhatsApp-style text, short voice note, watch glance, push, or full broadcast overlay), their **data budget**, their **attention budget**, their **language**, and how deep they want to go.

Same goal. An analyst on Wi-Fi gets a full overlay with xG and pressure numbers. A commuter in Jakarta on 1 MB gets a 160-character SMS in Bahasa. A fan in Lagos gets a 12-second voice note in Pidgin.

## 2. Why it's different

From a review of the ~470 projects on Innovation Studio (Oct 21): nearly all of them personalize by **taste** (analyst vs fan, club, player, language) and deliver to a **web screen or overlay**. None personalize by **connection, data cost, device, or attention**, and none deliver over SMS or sized voice notes. MatchGist covers the standard pipeline *and* adds that axis.

## 3. Hackathon fit

| Requirement (HACKATHON_BRIEF §2) | How MatchGist covers it |
|---|---|
| Ingest live synthetic events | Seeded simulator streams events at 1x/10x/60x |
| Interpret into stats and patterns | Stats Engine (pure code): possession, pass accuracy, pass difficulty, shot speed, xG, momentum, pressure |
| Explain why moments matter | Explainer agent, grounded only in Match State numbers |
| Render on screen | Broadcast channel emits timed overlay cue JSON, shown on a live pitch view. Every other channel is also a rendered output (SMS, voice, watch) |
| Personalize | Taste (mode, club, player, metric, language) **plus** constraints (channel, data budget, ping limit) |
| Narratives and recaps | Live gists plus a full-time Digest sized to the remaining budget |
| Multi-language | Demo set: English, Hindi, Bahasa Indonesia, Brazilian Portuguese, Arabic, Nigerian Pidgin |
| Data innovation | Documented synthetic event schema, seeded generator, storylines |

**Target prizes:** Grand Prize, Best Multi-Agent Orchestration, Best Use of Microsoft Foundry. Secondary: Best Azure Cloud Native (if Azure Communication Services SMS lands).

## 4. Hard rules

1. **Fictional clubs and players only.** No real names, crests, or league branding anywhere: code, tests, data, UI, video.
2. **Synthetic data only.** No real match footage or data.
3. **LLMs never invent numbers.** All stats come from code; agent output is checked against Match State.
4. **The feed never stops.** Timeouts, retries, template fallbacks.
5. Public GitHub repo. Live demo link with no login. Video under 2 minutes, no copyrighted music.

## 5. Fan profile

```json
{
  "fan_id": "fan_jakarta",
  "display_name": "Commuter in Jakarta",
  "language": "id",
  "mode": "casual",
  "favorite_club": "RIV",
  "favorite_player": null,
  "focus_metric": null,
  "channel": "sms",
  "data_budget_kb": 1024,
  "max_pings": 4,
  "only_if_involved": true,
  "quiet_after_minute": null
}
```

| Field | Values |
|---|---|
| `mode` | `analyst`, `casual`, `club_focus`, `player_focus`, `single_metric` |
| `channel` | `broadcast` (overlay), `sms`, `chat` (WhatsApp-style text), `voice` (voice note), `watch` (glance), `push` |
| `data_budget_kb` | Total data allowed for the match. `null` = unlimited |
| `max_pings` | Max messages for the match. `null` = unlimited |
| `only_if_involved` | Only send moments involving the favourite club/player |
| `language` | BCP-47 code: `en`, `hi`, `id`, `pt-BR`, `ar`, `pcm` (Nigerian Pidgin) |

### 5.1 Demo personas (seed these in `data/fans.json`)

| Persona | Language | Channel | Budget | Mode |
|---|---|---|---|---|
| Studio analyst, London | en | broadcast | unlimited | analyst |
| Commuter, Jakarta | id | sms | 1 MB, 4 pings | casual, only RIV |
| Fan, Lagos | pcm | voice | 2 MB, 6 pings | club_focus NOR |
| Office worker, São Paulo | pt-BR | push | 200 KB, 3 pings | casual |
| Student, Delhi | hi | sms | 1.5 MB | player_focus (RIV-10) |
| Fan roaming in Dubai | ar | watch | 300 KB, 5 pings | casual |

## 6. Channel limits and size model

All sizes are estimates computed in code, shown in the UI as a running "data used" meter.

| Channel | Limit per message | Size estimate |
|---|---|---|
| `sms` | 1 segment preferred, max 2 | GSM-7: 160 chars in one segment, 153 per segment when split; UCS-2 (Hindi, Arabic, emoji): 70 in one segment, 67 per segment when split. ~0.2 KB/segment |
| `chat` | 280 chars | UTF-8 byte length + 1 KB overhead |
| `voice` | 15 s | Opus at 16 kbps: `seconds × 16 ÷ 8` KB → 12 s ≈ 24 KB |
| `watch` | 40 chars + 1 number | UTF-8 bytes + 0.5 KB |
| `push` | title 50 chars + body 100 chars | UTF-8 bytes + 1 KB |
| `broadcast` | overlay cue | not budgeted |

**SMS encoding is the trap.** One non-GSM character (any Hindi or Arabic letter, many emoji, curly quotes) switches the whole message to UCS-2 and cuts the limit from 160 to 70 characters. The Compressor must count segments with a real encoder check, not character count.

### 6.1 Worked example (Jakarta commuter, 1 MB, 4 pings)

| Step | Calculation | Result |
|---|---|---|
| Budget | 1 MB = 1,024 KB | 1,024 KB |
| One SMS segment | ≈ 0.2 KB | 0.2 KB |
| 4 pings, 1 segment each | 4 × 0.2 | 0.8 KB |
| Full-time digest (3 segments) | 3 × 0.2 | 0.6 KB |
| Total | 0.8 + 0.6 | 1.4 KB, far under budget |

Here the binding limit is **pings, not data**, so the Budget Guard spends pings only on the four highest-scoring moments. For the Lagos voice persona (2 MB, 6 pings, 12 s notes ≈ 24 KB each), 6 × 24 = 144 KB, so again pings bind. Data binds for richer channels or long digests. The UI should show which limit is binding.

## 7. Architecture

```
Event Simulator ──► Stats Engine ──► Match State (shared)
   (seeded)          (pure code)          │
                                          ▼
                                   Moment Detector (rules)
                                          │ candidate moments
                                          ▼
                       ┌──────── Orchestrator (Microsoft Agent Framework) ────────┐
                       │                                                          │
                       │  Explainer ──► per fan: Relevance Ranker                 │
                       │                         │                                │
                       │                         ▼                                │
                       │                    Budget Guard ── skip / hold / send    │
                       │                         │                                │
                       │                         ▼                                │
                       │                    Localizer (language + football slang) │
                       │                         │                                │
                       │                         ▼                                │
                       │                    Compressor (fit limits, in target     │
                       │                                language)                 │
                       │                         │                                │
                       │                         ▼                                │
                       │                    Verifier (numbers + limits check)     │
                       │                                                          │
                       │  Digest Agent (full time, sized to remaining budget)     │
                       └──────────────────────────┬───────────────────────────────┘
                                                  ▼
                                      Delivery adapters (per channel)
                                                  ▼
                     Web UI: phone/watch simulators + broadcast overlay + System panel
```

### 7.1 Components

| # | Component | Type | Job |
|---|---|---|---|
| 1 | Event Simulator | Python, deterministic | Full 90-min match from a seed; storylines; playback at 1x/10x/60x |
| 2 | Stats Engine | Python, no LLM | Updates Match State per event. Only source of numbers |
| 3 | Match State | Shared store | Score, clock, team and player stats, momentum series, moments, per-fan delivery ledger |
| 4 | Moment Detector | Rules | Flags candidate moments (§9.1) with a base importance score 0–100 |
| 5 | Explainer | LLM (Foundry) | One neutral, English, stats-grounded explanation per moment (shared by all fans) |
| 6 | Relevance Ranker | Code + small LLM call | Scores the moment *for this fan* (club/player involvement, mode, focus metric) |
| 7 | Budget Guard | Code | Decides send now / hold for bundle / skip, using remaining pings, data, and upcoming match time. Records the reason |
| 8 | Localizer | LLM (Foundry) | Translates and adapts tone and football slang for the language and mode |
| 9 | Compressor | LLM (Foundry) | Rewrites the **localized** text to the channel's hard limit (§6), working in the target language. Runs after the Localizer because translation changes length and can switch SMS encoding to UCS-2 |
| 10 | Verifier | Code | Every number in the output exists in the Match State snapshot; channel limit met; SMS segment count correct |
| 11 | Voice adapter | Azure AI Speech (TTS) | Turns voice-channel text into audio; reports actual duration and size. Text fallback if TTS unavailable |
| 12 | Digest Agent | LLM (Foundry) | Full-time recap sized to the fan's remaining budget |
| 13 | Orchestrator | Microsoft Agent Framework | Runs the per-fan chain; handoffs, retries, fallbacks; emits `agent_events` |
| 14 | Delivery adapters | Python | `broadcast` → overlay cue; `sms`/`chat`/`push`/`watch`/`voice` → message objects for the simulator UI. Stretch: real SMS via Azure Communication Services |
| 15 | API | FastAPI + SSE | Streams events, stats, moments, deliveries, agent_events |
| 16 | Web UI | Next.js | Live pitch, persona devices side by side, data meters, System panel |

### 7.2 Why this is genuinely multi-agent

- **Shared state:** Match State and the per-fan delivery ledger (what was sent, data used, pings left).
- **Handoffs:** Explainer → Ranker → Budget Guard → Localizer → Compressor → Verifier, per fan, in parallel across fans. Order matters: compressing English and translating afterwards would break the limits.
- **Different roles a single agent does badly:** the Budget Guard plans across the whole match ("save a ping, the second half matters more"); the Compressor optimizes against hard byte limits; the Localizer handles language and slang; the Verifier is deterministic.
- **Recovery:** Verifier rejects → back to Compressor (max 2 retries) → template fallback. Every step is logged and visible in the System panel.

### 7.3 Failure handling

1. Every LLM call: 8 s timeout, 2 retries with backoff.
2. On failure, use a **template per channel and language** built from Match State (e.g., SMS: `GOAL {club} {score} ({minute}') {scorer}`).
3. Verifier failures and fallbacks are emitted as `agent_events` and shown in the UI.
4. If Azure AI Speech fails, the voice channel sends the text instead and marks it.

## 8. Data

### 8.1 Fictional clubs (`data/clubs.json`)

Riverside Athletic (`RIV`) vs Northgate Rovers (`NOR`). 16 players each: name, shirt number, position, pace/passing/shooting/defending (1–100). Varied names from many countries. Nothing matching a real player or club.

### 8.2 Event schema (v1)

```json
{
  "event_id": "m001-000412",
  "match_id": "m001",
  "seq": 412,
  "match_clock": "34:12",
  "period": 1,
  "type": "pass",
  "team_id": "RIV",
  "player_id": "RIV-08",
  "x": 46.2, "y": 31.0,
  "end_x": 71.5, "end_y": 18.4,
  "outcome": "complete",
  "receiver_id": "RIV-10",
  "pressure": 0.62,
  "speed_kmh": null,
  "meta": {}
}
```

Pitch: x 0–105 (own goal → opponent goal), y 0–68.

| type | Extra fields |
|---|---|
| `kickoff`, `half_time`, `full_time` | — |
| `pass` | `end_x`, `end_y`, `outcome` (complete/incomplete), `receiver_id` |
| `carry` | `end_x`, `end_y`, `distance_m`, `speed_kmh` |
| `shot` | `outcome` (goal/saved/off_target/blocked), `speed_kmh`, `xg` |
| `tackle` | `outcome` (won/lost), `opponent_id` |
| `interception` | — |
| `foul` | `card` (none/yellow/red) |
| `possession_change` | `from_team`, `to_team`, `cause` |
| `pressure` | `target_player_id`, `intensity` 0–1 |
| `substitution` | `player_off`, `player_on` |

### 8.3 Simulator

1. Seeded (`--seed 42`): same seed, identical match.
2. Possession-chain model; ratings affect pass success, shot speed, xG.
3. 1,200–1,800 events per match; realistic score.
4. Storylines: `none`, `comeback`, `red_card`, `late_drama` (decisive goal after 85').
5. Output to `matches/<id>.jsonl` or stream with `stream_events(match, speed)`.

## 9. Stats

| Stat | Definition |
|---|---|
| Possession % | Share of time in possession, rolling 5 min and full match |
| Pass accuracy | completed ÷ attempted |
| Pass distance | √((end_x − x)² + (end_y − y)²) |
| Pass difficulty (0–10) | `2.5·dist_norm + 3·pressure + 2·progressive + 2.5·into_final_third`, clipped to 10 |
| Shot speed | `speed_kmh` on shots |
| xG | from shot events; cumulative per team |
| Momentum (−100 to 100) | rolling 5 min: `+3 shot, +5 on target, +1 progressive pass, +2 tackle won in opp. half`, home − away, normalised |
| Pressure index | mean pressure faced by a team's passes, last 5 min |

`dist_norm = min(distance/40, 1)`; `progressive` = 1 if ball moves ≥ 10 m toward goal; `into_final_third` = 1 if the pass ends in the final third from outside it.

### 9.1 Moment triggers and base importance

| Trigger | Condition | Base score |
|---|---|---|
| Goal | shot outcome `goal` | 100 |
| Red card | foul with red | 85 |
| Big chance | xG ≥ 0.3, not a goal | 60 |
| Momentum swing | momentum changes sign and moves ≥ 40 in 5 min | 55 |
| Half time / full time | period events | 50 / 90 |
| Pressure spike | team pressure index +0.25 in 5 min | 40 |
| Elite pass | difficulty ≥ 8 and complete | 30 |
| Yellow card | foul with yellow | 25 |

Relevance Ranker adjusts per fan: +30 if favourite club involved, +40 if favourite player involved, −40 if `only_if_involved` and not involved (→ skip), +20 if it moves the fan's `focus_metric`.

### 9.2 Budget Guard rules (v1)

1. Goals and full time always send if any ping or data remains.
2. Otherwise send only if `adjusted_score ≥ threshold`, where the threshold rises as pings run out: `threshold = 50 + 40 × (1 − pings_left / max_pings)`.
3. Reserve 1 ping and enough data for the full-time digest from the 75th minute.
4. Moments within 2 match-minutes of each other can be bundled into one message.
5. Every decision stores a one-line reason (shown in the System panel).

## 10. Outputs

### 10.1 Delivery object (all channels)

```json
{
  "delivery_id": "d-0042",
  "fan_id": "fan_jakarta",
  "moment_id": "mom-0007",
  "channel": "sms",
  "language": "id",
  "match_clock": "67:40",
  "text": "GOL! RIV 2-1 NOR (67') Okafor. Serangan balik kilat, 6 umpan dalam 11 detik.",
  "audio_url": null,
  "size_kb": 0.2,
  "segments": 1,
  "encoding": "GSM-7",
  "budget_after": { "data_kb_left": 1023.6, "pings_left": 2 },
  "decision_reason": "Goal by favourite club; always send.",
  "fallback_used": false
}
```

### 10.2 Broadcast overlay cue

```json
{
  "cue_id": "cue-0091",
  "match_clock": "34:12",
  "show_at_ms": 2052000,
  "duration_ms": 6000,
  "slot": "lower_third",
  "template": "pass_quality",
  "data": { "player": "T. Okafor", "distance_m": 31.4, "difficulty": 8.6 },
  "text": "Elite pass: 31 m under heavy pressure"
}
```

Slots: `lower_third`, `top_bar`, `side_panel`, `player_tag`.

## 11. Tech stack

| Layer | Choice |
|---|---|
| Backend | Python 3.11+, FastAPI, SSE |
| Agents | Microsoft Agent Framework (Python) |
| Models | Microsoft Foundry: `gpt-4o-mini` for all live agents; optionally a stronger model for the Digest only |
| Voice | Azure AI Speech (text to speech). Check which voices exist for each demo language; fall back to text where none exist |
| SMS (stretch) | Azure Communication Services SMS |
| State | In-memory + SQLite |
| Frontend | Next.js + Tailwind |
| Hosting | Azure Container Apps, consumption plan |
| CI | GitHub Actions: ruff, pytest, build |
| Dev env | Windows + PowerShell |

### 11.1 Environment variables (`.env`, never committed)

```
AZURE_AI_PROJECT_ENDPOINT=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT_FAST=gpt-4o-mini
AZURE_OPENAI_DEPLOYMENT_DIGEST=
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=
ACS_CONNECTION_STRING=
SIM_SEED=42
SIM_SPEED=10
```

## 12. Repo structure

```
matchgist/
├─ README.md
├─ CLAUDE.md
├─ HACKATHON_BRIEF.md
├─ SPEC.md
├─ .env.example
├─ docs/
│  ├─ PROGRESS.md
│  ├─ event-schema.md
│  └─ architecture.md
├─ data/
│  ├─ clubs.json
│  └─ fans.json
├─ backend/
│  ├─ pyproject.toml
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ config.py
│  │  ├─ simulator/   (schema.py, engine.py, storylines.py, __main__.py)
│  │  ├─ stats/       (engine.py, metrics.py)
│  │  ├─ state/       (match_state.py, ledger.py)
│  │  ├─ moments/     (detector.py)
│  │  ├─ fans/        (profiles.py)
│  │  ├─ channels/    (limits.py, sms_encoding.py, sizing.py, adapters.py)
│  │  ├─ agents/      (orchestrator.py, explainer.py, ranker.py, budget_guard.py,
│  │  │               compressor.py, localizer.py, verifier.py, digest.py, fallbacks.py)
│  │  └─ voice/       (tts.py)
│  └─ tests/
├─ frontend/
├─ infra/
└─ .github/workflows/ci.yml
```

## 13. API

| Method | Path | Purpose |
|---|---|---|
| POST | `/matches` | Start a match `{seed, speed, storyline}` → `match_id` |
| GET | `/matches/{id}/stream` | SSE: events, stats, moments, deliveries (all fans), overlay cues, agent_events |
| GET | `/matches/{id}/state` | Match State snapshot |
| GET | `/matches/{id}/fans/{fan_id}/ledger` | Everything sent to a fan, data used, pings left |
| GET | `/matches/{id}/fans/{fan_id}/digest` | Full-time digest |
| GET/POST | `/fans` | List personas / create a custom one |
| GET | `/health` | Health check |

## 14. UI (one screen, built for a 1080p recording)

1. **Top:** scoreboard, clock, speed control (1x / 10x / 60x), storyline picker.
2. **Left:** compact live pitch with the broadcast overlay cues (the analyst view).
3. **Centre:** a row of device mock-ups, one per persona: SMS phone, chat phone, voice-note phone (play button + waveform), watch, push banner. Each shows a **data meter** and **pings left**, and which limit is binding.
4. **Right:** **System panel**: live agent_events (handoffs, Budget Guard decisions with reasons, Verifier rejections, fallbacks).
5. **Add a fan** button: pick language, channel, budget, mode, and watch them join live.
6. **Full time:** each device receives its digest.

## 15. Milestones

| # | Day | Milestone | Done when |
|---|---|---|---|
| M1 | Wed Oct 21 | Repo, schema, simulator, fan personas | `python -m app.simulator --seed 42` writes a full match; tests pass; `data/fans.json` has the 6 personas |
| M2 | Thu Oct 22 | Stats Engine, Match State, Moment Detector, channel limits + SMS encoding, SSE stream | Stats unit-tested; moments detected; SMS segment counter tested with GSM-7 and UCS-2 text |
| M3 | Fri Oct 23 | Agents: Explainer, Ranker, Budget Guard, Localizer, Compressor, Verifier, fallbacks (Agent Framework + Foundry) | One match streams deliveries for all 6 personas within limits; fallback works with the model disabled |
| M4 | Sat Oct 24 | Voice (Azure AI Speech), Digest, broadcast overlay cues | Voice notes play with real duration and size; digests fit remaining budget |
| M5 | Sun Oct 25 | Frontend | Full screen per §14 working end to end |
| M6 | Mon Oct 26 | Deploy + docs | Public URL on Azure Container Apps; README; architecture diagram; budget alert |
| M7 | Tue Oct 27 | Video + submit | Video under 2 min; submitted by 11:00 PM WAT |

Stretch, only if ahead: real SMS via Azure Communication Services to your own phone, shown in the video.

## 16. Demo video (under 2 min)

| Time | Shot |
|---|---|
| 0:00–0:12 | Hook: "Most of the world doesn't watch football on a big screen with fast Wi-Fi." |
| 0:12–0:30 | Start a match at 60x. Pitch and analyst overlay update |
| 0:30–0:55 | A goal. Same moment lands six ways: overlay, Bahasa SMS (160 chars), Pidgin voice note (play it), Hindi chat, Portuguese push, Arabic watch glance |
| 0:55–1:15 | Budget Guard: a near miss is skipped for the Jakarta fan ("saving pings, 1 left"); data meters move |
| 1:15–1:30 | System panel: Verifier rejects a 72-char Hindi SMS (UCS-2 limit 70), Compressor rewrites it |
| 1:30–1:45 | Full time: each device gets a digest sized to what's left |
| 1:45–1:58 | Architecture: Foundry, Agent Framework, AI Speech, Container Apps. Repo link |

## 17. README checklist

1. What it is (3 lines) and a GIF of the six devices
2. Live demo link (no login)
3. Architecture diagram
4. Microsoft tech used and where
5. Run locally (PowerShell)
6. Event schema and fan profile docs
7. How agents coordinate, decide, and recover
8. Channel size model and SMS encoding notes
9. Statement: all clubs, players, matches, and fans are fictional

## 18. Submission checklist

- [ ] Public GitHub repo
- [ ] Live demo URL, no login
- [ ] Video < 2 min on YouTube
- [ ] Pitch text (see PROJECT_PAGE.md)
- [ ] No real club or player names anywhere
- [ ] Submitted by Tue Oct 27, 11:00 PM WAT
