# Progress

_Last updated: Wed Oct 21 (end of M2, a day early)._

## Milestones (SPEC section 15)

| # | Day | Milestone | Status |
|---|---|---|---|
| M1 | Wed Oct 21 | Repo, schema, simulator, fan personas | ✅ done |
| M2 | Thu Oct 22 | Stats Engine, Match State, Moment Detector, channel limits + SMS encoding, SSE stream | ✅ done |
| M3 | Fri Oct 23 | Agents: Explainer, Ranker, Budget Guard, Localizer, Compressor, Verifier, fallbacks | ⏳ next |
| M4 | Sat Oct 24 | Voice (Azure AI Speech), Digest, broadcast overlay cues | ☐ |
| M5 | Sun Oct 25 | Frontend | ☐ |
| M6 | Mon Oct 26 | Deploy + docs | ☐ |
| M7 | Tue Oct 27 | Video + submit (by 11:00 PM WAT) | ☐ |

## M2: what was built

- **Channels** (`app/channels/`):
  - Real GSM-7 vs UCS-2 detection. Extension characters cost two septets, astral emoji cost two UTF-16 units, and neither is ever split across segments. Single SMS: 160/70; concatenated: 153/67 per segment.
  - Hard limits per channel with readable reasons.
  - The SPEC 6 size model.
  - 32 tests, including the 160/161 and 70/71 boundaries and the Jakarta worked example (1.4 KB).
- **Stats Engine** (`app/stats/`): SPEC 9 formulas as pure functions, folded into the **Match State** (`app/state/match_state.py`):
  - team and player stats
  - rolling 5-minute possession, momentum and pressure index
  - per-minute series
  - `snapshot()`, the set of numbers agents may cite
- **Moment Detector** (`app/moments/`): SPEC 9.1 triggers with base scores, each moment carrying its facts. A goal includes the assist and its pass difficulty; half-time and full-time include xG, shots, possession and the top performer. About 17 candidate moments per match.
- **Live stream** (`app/runtime.py`, `GET /matches/{id}/stream`, `GET /matches/{id}/state`, `GET /matches`): one shared playback per match, SSE with a snapshot first, keepalives, and slow viewers dropped. Four demo matches (seed 42, every storyline) are generated at startup.
- 74 tests, ruff clean. The test-client deprecation warning is silenced.

## Decisions taken

| Decision | Why |
|---|---|
| Reuse the Touchline prototype rather than start from zero | Saves about a day |
| Delhi persona uses **SMS** (Hindi, UCS-2) instead of chat | The video's "Verifier rejects a 72-char Hindi SMS" moment needs a real UCS-2 SMS persona |
| Team-relative coordinates; second-half clock restarts at 45:00 | SPEC "own goal → opponent goal"; broadcast convention |
| Standalone `pressure` events only for genuine presses | Keeps matches in the 1,200–1,800 event range |
| Storylines = biased plan + deterministic sub-seed search | Same seed always gives the same match; ~4 s average |
| **Elite pass threshold 9.5, not SPEC's 8** | With the SPEC formula, any long ball into the final third with a little pressure scores 8 (~20 a match). 9.5 gives ~3–4. It's one constant (`ELITE_PASS_DIFFICULTY`) if you want SPEC's value back. |
| On-target shot = 5 momentum points (not 3 + 5) | SPEC wording is ambiguous; "instead of" reads naturally |
| Momentum normalised with a floor of 25; a swing also needs the new leader at ≥ 25 and a 10-minute cooldown | Without this the 5-minute momentum flips about 12 times a match. Now about 4. |
| Pass `pressure` is convex in the nearest opponent's distance (0 beyond 3.5 m, 0.25 at 2 m, 0.69 at 1 m) | The linear curve put 57% of passes above 0.5. Now it's 31%, with a median of 0.17. |
| One playback per match shared by all viewers | M3 deliveries are computed once per fan and seen identically by everyone |

## Open decisions / risks

1. **Commits:** you push manually (no Claude attribution in commits). Code reaches you as a git bundle.
2. **Repo name:** keep `Touchline` or use `matchgist` (six other entries use "Touchline").
3. **Brazilian Portuguese SMS:** ç, ã, õ, ê, á and í are not GSM-7, so most pt-BR text costs UCS-2 (70 chars). The São Paulo persona is on push, so this doesn't bite in the demo, but the M3 Compressor should know it. Option: an accent-stripping GSM fallback for Latin-script languages, with the trade-off shown in the System panel.
4. **Nigerian Pidgin voice (M4):** check Azure AI Speech for `pcm`. Likely fallback: an `en-NG` neural voice reading Pidgin text, labelled.
5. **Model (M3):** confirm `gpt-4o-mini` is deployable in your Foundry region before pinning.
6. **Northgate is the stronger club** (about 60% of seed-sweep wins). Fine for storylines; the demo uses seed 42 per storyline anyway.
