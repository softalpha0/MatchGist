# Innovation Studio project page — MatchGist

Copy each block into the matching field on your project page.

---

## Title (max 140)

```
MatchGist: the match, sized to fit every fan
```

## Tagline (max 300)

```
Not every fan watches on a big screen with fast Wi-Fi. MatchGist explains what happened and why it mattered, then fits it to what each fan has: an SMS, a short voice note, a watch glance or a full overlay, in their language and within their data budget.
```

## Keywords (press Enter after each)

`Multi-Agent` · `Microsoft Foundry` · `Agent Framework` · `Low Bandwidth` · `SMS` · `Voice Notes` · `Personalization` · `Multilingual` · `Explainable AI` · `Synthetic Data`

## Description (Markdown)

```
Most match-intelligence tools assume you're watching on a big screen with fast internet. A lot of football fans aren't. They follow the game on mobile data, at work, on the bus, roaming abroad, or on a basic phone.

MatchGist takes a live stream of synthetic match events, works out which moments matter and why, and then delivers them in a form each fan can actually use.

**What each fan sets**
- **Channel:** SMS, chat message, short voice note, smartwatch glance, push notification, or a full broadcast overlay
- **Data budget:** for example, "keep this match under 1 MB"
- **Ping limit:** for example, "message me 4 times at most, only when my team is involved"
- **Language:** demo set is English, Hindi, Bahasa Indonesia, Brazilian Portuguese, Arabic and Nigerian Pidgin
- **Depth:** analyst numbers or plain-language summaries

**How it works**
- A Stats Engine (plain code) turns events into possession, pass difficulty, xG, momentum and pressure. The models never make up numbers.
- An Explainer agent writes why each moment matters, using only those stats.
- For every fan, a chain of agents runs in parallel: a Ranker scores how much the moment matters to that fan, a Budget Guard decides whether to send it now, bundle it or save the ping for later, a Localizer puts it in the fan's language, and a Compressor then fits it to the channel's hard limit in that language (160 characters for SMS, 70 if the language needs Unicode, about 15 seconds for a voice note).
- A Verifier checks every number and every limit before anything is sent. If a model call fails, a template takes over so the fan still gets the update.
- At full time, each fan gets a recap sized to whatever budget they have left.

The same goal can reach an analyst as an on-screen graphic, a commuter in Jakarta as one SMS in Bahasa, and a fan in Lagos as a 12-second voice note in Pidgin.

Built with Microsoft Foundry, Microsoft Agent Framework, Azure AI Speech, FastAPI, Next.js and Azure Container Apps. All clubs, players, matches and fans are fictional.

Target category: Best Multi-Agent Orchestration (also eligible for Best Use of Microsoft Foundry).
```

## Skills needed (only if you open the team)

`Next.js` · `Azure` · `Video Editing` · `Translation / Localization`
