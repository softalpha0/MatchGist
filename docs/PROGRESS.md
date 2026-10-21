# Progress

_Last updated: Wed Oct 21 (end of M1)._

## Milestones (SPEC section 15)

| # | Day | Milestone | Status |
|---|---|---|---|
| M1 | Wed Oct 21 | Repo, schema, simulator, fan personas | ✅ done |
| M2 | Thu Oct 22 | Stats Engine, Match State, Moment Detector, channel limits + SMS encoding, SSE stream | ⏳ next |
| M3 | Fri Oct 23 | Agents: Explainer, Ranker, Budget Guard, Localizer, Compressor, Verifier, fallbacks | ☐ |
| M4 | Sat Oct 24 | Voice (Azure AI Speech), Digest, broadcast overlay cues | ☐ |
| M5 | Sun Oct 25 | Frontend | ☐ |
| M6 | Mon Oct 26 | Deploy + docs | ☐ |
| M7 | Tue Oct 27 | Video + submit (by 11:00 PM WAT) | ☐ |

## M1: what was built

- Repo restructured to SPEC section 12. The earlier Touchline prototype lives in `legacy/` as a source of parts
  (its stats, verifier, supervisor and Agent Framework wiring get reused in M2/M3) and is deleted before submission.
- Event schema v1: Pydantic discriminated union for all 12 event types, documented in `docs/event-schema.md`.
- Simulator: seeded, deterministic possession-chain model with ratings. Includes throw-ins, corners,
  substitutions, cards and four storylines. CLI plus `stream_events` / `astream_events`.
- `data/clubs.json` (RIV, NOR; 16 fictional players each), `data/fans.json` (6 personas).
- API: `GET /health`, `POST /matches`, `GET /fans`.
- 24 tests (determinism, schema, counts, clock/seq order, coordinates, ratings effect, storylines, personas, API). CI runs ruff and pytest.

## Decisions taken

| Decision | Why |
|---|---|
| Reuse the Touchline prototype rather than start from zero | Saves about a day. The simulator, verifier and Agent Framework wiring already worked and were tested. |
| Delhi persona uses **SMS** (Hindi, UCS-2) instead of chat | The video's "Verifier rejects a 72-char Hindi SMS" moment needs a real UCS-2 SMS persona. SPEC table updated. |
| Team-relative coordinates | SPEC says "own goal → opponent goal". Renderers mirror. |
| Second-half clock restarts at 45:00; order by `(period, clock)` | Matches broadcast convention; first-half stoppage time shows as 45:xx–48:xx |
| Standalone `pressure` events only for genuine presses (8 m → 1.2 m) | Keeps the match in SPEC's 1,200–1,800 event range. The `pressure` value on each pass still captures every challenge. |
| Storylines = biased plan + deterministic sub-seed search | Same seed always gives the same match. Generation averages ~4 s (worst case seen: 10 s). |

## Open decisions / risks

1. **GitHub push is blocked (HTTP 403).** The Claude GitHub App needs write access to `softalpha0/Touchline` (or a new `matchgist` repo). All commits exist only locally until then.
2. **Repo name:** stay on `Touchline` or create `matchgist` (the brief says six other entries use "Touchline").
3. **Nigerian Pidgin voice (M4):** check whether Azure AI Speech has `pcm`. Likely fallback: an `en-NG` neural voice reading Pidgin text, labelled.
4. **Model (M3):** confirm `gpt-4o-mini` is still deployable in your Foundry region before pinning.
5. Storyline generation averages ~4 s (max 10 s seen). For the demo, pre-generate seed 42 for each storyline at start-up in M2.
6. Simulator calibration is done (see docs/event-schema.md). Northgate is the slightly stronger club; Riverside's style changed from possession to balanced to keep the fixture competitive.
