# Progress

_Last updated: Wed Oct 21 (M3–M5 built; M6 packaged, waiting on your Azure accounts)._

## Milestones (SPEC section 15)

| # | Day | Milestone | Status |
|---|---|---|---|
| M1 | Wed Oct 21 | Repo, schema, simulator, fan personas | ✅ done |
| M2 | Thu Oct 22 | Stats Engine, Match State, Moment Detector, channel limits + SMS encoding, SSE stream | ✅ done |
| M3 | Fri Oct 23 | Agents: Explainer, Ranker, Budget Guard, Localizer, Compressor, Verifier, fallbacks | ✅ done (offline-verified; needs a live model check) |
| M4 | Sat Oct 24 | Voice (Azure AI Speech), Digest, broadcast overlay cues | ✅ built; voice needs a Speech key to verify |
| M5 | Sun Oct 25 | Frontend | ✅ done: landing page + live demo |
| M6 | Mon Oct 26 | Deploy + docs | 🟡 Dockerfile, CI image publish, deploy script and docs ready; **you** run the deploy |
| M7 | Tue Oct 27 | Video + submit (by 11:00 PM WAT) | ☐ |

## What's built

- **Agents** (`backend/app/agents/`): Explainer once per moment. Then, per fan in parallel, a Microsoft Agent
  Framework workflow: Ranker → Budget Guard → Localizer → Compressor ⇄ Verifier → deliver, plus a Digest at full
  time. Each model call has an 8 s timeout and 2 retries, falling back to per-channel, per-language templates
  (9 moment types × 6 languages). Backends: Azure OpenAI (key), Foundry project (Entra ID), or offline.
- **Budget Guard:** SPEC 9.2 plus planning. The last two pings are kept for a goal and the digest, close moments
  are bundled within 2 minutes, half-time and red cards send immediately, and every decision carries a reason.
- **Verifier:** numbers must come from the moment's facts (digits in any script); SMS segment allowance from the
  Guard; all channel limits.
- **Voice:** Azure AI Speech REST, Ogg/Opus with real duration and size; text fallback when not configured.
  Pidgin is read by `en-NG-EzinneNeural` (labelled).
- **Overlay cues** for the broadcast persona (SPEC 10.2).
- **Runtime/API:** deliveries and agent events on the SSE stream; replay, add-a-fan, ledger, digest, audio and
  config endpoints.
- **Frontend** (`frontend/`): Next.js 15 + Tailwind 4 static export served by FastAPI. Landing page; `/live` with
  pitch and overlay, devices with data meters, pings and binding limit, System panel, Add a fan.
- **Ops:** multi-stage Dockerfile, CI (backend, frontend, image build + smoke test + GHCR publish),
  `infra/deploy.ps1`, `docs/deploy.md`, `docs/architecture.md`, full README.
- **Tests:** 171 backend tests, all offline. They include a model outage, a hallucinating model, the Hindi SMS
  reject-and-rewrite loop, and budget limits for every persona.

## Decisions taken (new in M3–M5)

| Decision | Why |
|---|---|
| Ranker is pure code (no model call) | SPEC allows "code + small LLM call"; rules give visible, testable reasons |
| Deliveries verified against the moment's facts, not the whole snapshot | The full snapshot has so many small integers that "his 9th goal in 3 games" passed. Facts-only is the real guarantee. |
| Budget Guard keeps the last 2 pings for a goal + digest | Without it, Jakarta's 1 MB/4-ping fan missed their own club's 90th-minute goal |
| Half-time and red cards are never held for a bundle | A held HT was bundled after a second-half goal ("Plus: HT 0-0") |
| Verifier sends an immutable `Verified` message on the retry loop | Workflow edge conditions were evaluated after the job mutated, so a rejected text could also reach Deliver |
| Accent stripping for Latin-script SMS when it saves a segment | One "í" in a scorer's name pushed a Bahasa digest into UCS-2 |
| Arabic text isolates Latin names (U+2068/U+2069) | "Okeke-Rhodes" was split by the bidi algorithm on the watch |
| Next.js static export served by FastAPI | One container, one URL, no Node server in production |
| Image published to GitHub Container Registry | No Azure Container Registry cost |

## What's left (yours unless noted)

1. **Push the code** (you push manually) and make the GitHub repo public. Decide the repo name; the landing
   page's "Read the code" link points at `github.com/softalpha0/matchgist`.
2. **Foundry model:** deploy a small chat model. ⚠️ `gpt-4o-mini` is reportedly retired on Azure in 2026; pick the
   current mini model. Put the endpoint, key and deployment in `.env`, then run a match and check `/config` says
   `azure-openai`. I'll then tune prompts against real output (the agent code hasn't run against a live model yet).
3. **Speech:** create a free F0 Speech resource, set the key and region, and confirm the voices exist.
4. **Deploy** with `infra/deploy.ps1` (after the $50 budget alert). Put the URL in the README. Open `/live` in a
   private window.
5. **Video** (< 2 min) following SPEC section 16, then **submit** by Tue Oct 27, 11:00 PM WAT.
6. Housekeeping before submission (ask me):
   - delete `legacy/`
   - decide whether `SPEC.md`, `HACKATHON_BRIEF.md` and `CLAUDE.md` stay in the public repo (they mention the
     real league's name in the challenge title)
7. Stretch (not done): real SMS via Azure Communication Services.
