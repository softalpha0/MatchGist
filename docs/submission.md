# MatchGist: submission text

## The problem

A football match reaches millions of fans at once, but match intelligence assumes a big screen, fast data and
English. A commuter on a 1 MB plan, a student reading Hindi by SMS, a fan roaming abroad with only a watch: they
get a scoreline, or a truncated English sentence. Their limits are hard ones. Data costs money, every ping
interrupts, and one Hindi or Arabic letter turns a 160-character SMS into a 70-character one.

## What MatchGist does

Open the live demo and one synthetic match plays next to six fictional fans: a studio analyst in London (broadcast
overlay), a commuter in Jakarta (SMS in Bahasa, 1 MB, 4 pings, follows one club), a fan in Lagos (voice notes in
Pidgin), a student in Delhi (SMS in Hindi, follows one player), an office worker in São Paulo (push in Portuguese,
200 KB) and a fan roaming in Dubai (watch in Arabic). The same goal reaches each of them differently: an overlay
cue with xG for the studio, one 0.2 KB GSM-7 segment in Bahasa, a 70-character UCS-2 Hindi SMS, a 40-character
Arabic watch glance plus "1-2". Each device shows the bytes used against the budget, pings left, and which limit
binds. Minor moments are held and bundled, and the last two pings are kept for a goal and the full-time digest.

## How it uses the synthetic match events

Our seeded simulator generates about 1,300 football-realistic events per match: passes, carries, shots, tackles,
pressure, possession changes, cards and substitutions, with pitch coordinates and fictional players. A Stats
Engine computes possession, pass difficulty, xG, momentum and a pressure index; it is the only source of numbers.
A Moment Detector turns state changes into moments (goals, big chances, momentum swings, pressure spikes, cards,
half-time, full-time), each with its facts and its source events. Four storylines are recorded: late drama, a
comeback, a red card and an open game.

## How it makes insights explainable

Detected facts and narrative are kept apart. Code detects the facts; the model only writes words around them.
Every moment stores the events that triggered it, and every message stores its moments. Tap "why?" under any
message to see the facts, the six source events (time, type, player, team, coordinates), the Budget Guard's
decision and each agent step. A Verifier checks every digit in every message against the facts, in any script,
and every channel limit with real GSM-7 / UCS-2 segment counting. A rejected message goes back to the Compressor
with the exact reason; after two tries, a per-language template takes over. The feed never stops.
The `evidence/` folder holds these trails for four full matches: 193 messages, all model-written and verified,
6 drafts rejected and fixed on retry, 0 template fallbacks.

## How it's built

Microsoft Agent Framework runs the multi-agent system: an Explainer once per moment, then a separate workflow
per fan (Ranker → Budget Guard → Localizer → Compressor ⇄ Verifier) with conditional edges and a retry loop, and
a Digest agent at full time. The language agents call a chat model through an OpenAI-compatible client; the code
also supports Microsoft Foundry and Azure OpenAI, and has an Azure AI Speech adapter and an Azure Container Apps
deploy script. We could not open an Azure subscription in time, so the public demo is a static site on Netlify
that plays recorded runs of the full pipeline, and the agent server runs from the same repository with one
command. 178 tests run on every push in GitHub Actions.

## What's next

Real delivery through SMS and push gateways; a Verifier for names and numbers written as words; native-speaker
review of the six languages; running the agents on Microsoft Foundry with Azure AI Speech voice notes; and
letting fans set their own budget and channel in a companion app.
