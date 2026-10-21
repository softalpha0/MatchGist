# Hackathon Brief — Inside the Game: Developer Hackathon

Condensed from the organizers' public repo: https://github.com/microsoft/insidethegamehackathon
(Official Rules, Resource Playlists, Code of Conduct). The Official Rules always win if anything here differs.

Innovation Studio challenge name: **The Synthetic Match Insights Engine for Premier League Studio**

---

## 1. Dates (WAT = Pacific Time + 8h in October)

| Stage | Pacific Time | WAT |
|---|---|---|
| Build / submission period | Oct 6, 9:00 AM → Oct 27, 11:59 PM | Oct 6, 5:00 PM → **Wed Oct 28, 7:59 AM** |
| Judging | Oct 27 → Nov 10 | — |
| Winners announced | by Nov 20 | — |

Internal target: **submit by Tue Oct 27, 11:00 PM WAT** (9 hours of buffer).

## 2. The challenge (paraphrased)

Build an AI-driven app or set of agents that turns **synthetic football events** into **explainable match intelligence**: meaningful stats, key moments, why they matter, real-time narratives, automated recaps for studio/broadcast/streaming use, and personalized experiences for fans in any market.

### 2.1 Required pipeline (five stages)

| Stage | Requirement |
|---|---|
| Ingest | Take in synthetic match events as they happen (passes, shots, tackles, possession changes, pressure events, match metadata) |
| Interpret | Turn them into football statistics, patterns, and context |
| Explain | Say why a moment matters, not only that it happened |
| Render | Produce output that can sit on screen alongside the match. Timed, machine-readable, renderable as synchronized graphical overlays on a live feed |
| Personalize | Same intelligence, genuinely different experiences for a data-hungry analyst vs a casual fan. Ideas named: custom modes, favourite club(s), favourite player(s), player-focus mode that follows one player all match, language preference, a single metric the viewer cares about |

The organizers state that a project with only metrics has no audience, and a project with only personalization has nothing to personalize. **We must do both.**

### 2.2 Suggested features (cover as many as practical)

| Area | Feature |
|---|---|
| Real-time intelligence | Player identification: live name tags, optional speed and distance indicators triggered at thresholds |
| | Pass quality: distance, accuracy, difficulty rating |
| | Speed metrics: ball speed, shot speed |
| | Auto-eventing: a model over a video feed generating pass and speed metrics automatically (stretch goal) |
| Narrative | Key narratives, player-performance context, milestones, match recaps |
| Explainability | Control vs chaos, tactical pressure changes, game rhythm patterns |
| Data innovation | Create or extend synthetic, football-realistic datasets (passes, shots, tackles, possession changes, pressure, metadata) |
| Multi-language | Clear natural-language output in multiple languages |

## 3. Hard rules for the build

1. **Synthetic data only.** No match footage or data is provided; anything we use must be ours or properly licensed. We generate everything.
2. **No third-party trademarks or copyrighted material** in the project or video without permission. Use fictional clubs and players. No real club names, crests, player names, or league branding.
3. **New project only.** Created after Sept 29, 2026.
4. **Original work.** Open-source libraries are allowed if we follow their licences and build meaningfully on top.
5. **Must actually run** as shown in the video and description.
6. **Testable by judges free of charge.** Provide a working link or test build. If login is needed, include credentials in testing instructions. Aim for no login.
7. **English** for all submission materials.
8. Nothing offensive, political, or promoting alcohol, drugs, or tobacco.

## 4. Submission requirements

| # | Item | Notes |
|---|---|---|
| 1 | Project pitch / description | What we built, which Microsoft and Azure tech, what it does, what problem it solves |
| 2 | Demo video | **Under 2 minutes**; shows the project running; public URL on YouTube, Vimeo, Facebook Video, or Youku; no copyrighted music |
| 3 | GitHub repo URL | **Must be public** |
| 4 | Testing access | Live link or test build, free and unrestricted until judging ends |

Submitted through the project page on Innovation Studio.

## 5. Judging

**Stage 1 (pass/fail):** fits the theme and reasonably uses the required technologies.

**Stage 2 (20% each):**

| Criterion | What judges look for | How we score |
|---|---|---|
| Technological implementation | Creative, optimized synthetic data; good engineering practice; effective use of hero tech; clean, documented, maintainable code | Seeded simulator, tests, CI, typed code, README, Foundry + Agent Framework at the core |
| Agentic design and innovation | Creative agentic patterns; orchestration, MCP, or multi-agent collaboration; novel AI use | Budget Guard plans across the whole match; Compressor works against hard byte limits; Verifier loop; per-fan parallel chains; visible decisions and recovery |
| Real-world impact | Significant problem; production-ready potential; impact on users | Serves fans the big-screen tools ignore (mobile data, roaming, basic phones, at work); real channel constraints (SMS encoding, voice note size); overlay cues for broadcasters too |
| User experience and presentation | Intuitive UX; clear demo video; balance of frontend and backend | One goal landing six ways on six devices, with live data meters |
| Category fit | Matches the chosen category description | See §6 |

Tie-break order follows the criteria order above, so **technological implementation matters most in a tie**.

**Hero technologies named by the organizers:** Microsoft Foundry, Microsoft Agent Framework, Azure MCP, GitHub Copilot Agent Mode, Microsoft Fabric, GitHub SDK, GitHub CLI, Azure Apps and AI Services, Azure databases.

## 6. Prize categories

A project can win one Grand Prize and up to one Category Prize. Judges may move a project to a better-fitting category.

| Prize | What wins it | Per-person value (approx.) |
|---|---|---|
| Grand Prize 1st | Most complete, compelling solution; innovative use of Microsoft AI stack; strong explainable intelligence and personalization | $4,000 + PL match ticket + $50 store voucher |
| Grand Prize 2nd | Runner-up on the same terms | $2,500 + ticket + voucher |
| Best Use of Microsoft Foundry | Foundry clearly speeds up building, orchestrating, and managing the AI | $1,500 + voucher |
| Best Enterprise Solution | Ready for enterprise deployment: reliability, transparency, controls | $1,500 + voucher |
| **Best Multi-Agent Orchestration** (our target; the rules call it "Best Multi-Agent System") | Agents with distinct roles, coordinating via shared state and handoffs, recovering from failures, achieving an end-to-end result one agent couldn't. GitHub Copilot, Agent Framework, A2A, or other orchestration | $1,500 + voucher |
| Best Azure Cloud Native Integration | AKS, Container Apps, Functions, Logic Apps, AI data platforms; event-driven, automated, operationally sound | $1,500 + voucher |

## 7. Official learning resources (AI Skills Navigator)

| Playlist | Link |
|---|---|
| GitHub Copilot | https://aka.ms/asn/ghcopilot |
| Azure AI Foundry | https://aka.ms/asn/foundry |
| Foundry Agents | https://aka.ms/asn/foundryagents |
| Agentic Workflows | https://aka.ms/asn/agenticworkflows |
| Data | https://aka.ms/asn/data |

Also referenced in the rules: Microsoft Learn (https://learn.microsoft.com) and the Azure Architecture Center best practices (https://learn.microsoft.com/en-us/azure/architecture/best-practices/index-best-practices).

## 8. Innovation Studio overview page (checked Oct 21)

- Matches the Official Rules on prizes, submission requirements, judging rubric and dates.
- Competition size at the time: **1,749 registrants, 472 projects.** Polish and a clear demo matter.
- Repeats the data rule: synthetic, football-realistic data only; no real Premier League data is provided.
- Says the full challenge brief and detailed project requirements are under the **Challenge** menu. Add anything new from there to this file.

## 9. Competitor landscape (review of ~470 projects, Oct 21)

**The crowded middle (avoid looking like this):** multi-agent pipeline + evidence-checked explanations + analyst/casual modes + multilingual + broadcast overlays. Dozens of entries: many named MatchMind, MatchLens, PitchPulse, Pitchside, The Gallery, plus six projects using "Touchline". Verifier-style "every claim is proven" is now common, so it's table stakes, not a differentiator.

**Already-claimed niches:**

| Niche | Projects |
|---|---|
| Auto video reels / highlights | auto-shorts, PitchClip AI, Dugout, Footlights, FansReel |
| Accessibility / spatial audio | Audio Eyes, Blind-side, Sauti |
| Swahili / Arabic / Urdu / Japanese | Sauti, Msimulizi, Matchday Crew, EveryFan, MatchMind Booth |
| What-if / counterfactual | Second Guess, PULSE XI, ParallelPitch, Chronos XI, ReplayAI |
| Rival-fan or pundit debate | Both Ends, Pundit Studio |
| Referee explanations | Matchday Explainer, CaptionVAR Live |
| Human-in-the-loop control room | Control Room IQ, Gallery, MatchDesk |
| Prediction / odds | Knife-Edge, Lasso, Risk Radar |
| New-fan teaching | Coach in Your Ear, Standfolk |

**Open lane we take:** personalization by **constraint** (channel, data budget, ping limit, device) with delivery over SMS, chat, voice notes, watch, and push. No project found covers it.

**How to stand out in judging:**
1. Lead every description and the video with the constraint angle, not "multi-agent explainable insights" (everyone says that).
2. Show numbers judges can check: SMS segments, KB used, pings left.
3. Still cover the standard pipeline fully (broadcast overlay channel, analyst mode) so we pass Stage 1 on theme.
