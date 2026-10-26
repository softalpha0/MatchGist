# none: Riverside Athletic 1-2 Northgate Rovers

Seed 42, model `openai-compatible:gpt-6-luna`, recorded 2026-10-26 04:04 UTC.
Synthetic match, fictional clubs and players.

1402 events, 16 moments, 44 deliveries to 6 fans.

## Grounding check (the Verifier)

| Result | Count |
|---|---|
| Verifier passed | 44 |
| Verifier rejected, sent back to the Compressor | 0 |
| Fell back to a template after rejections | 0 |
| Deliveries written by the model (and verified) | 44 |
| Deliveries from a fallback template | 0 |

Template fallbacks by agent: explainer 1.

## Moments and their source events

### 03:46 goal (`demo-none-mom-0001`)

Facts: minute=4, match_clock=03:46, score=0-1, team_code=NOR, player=Joaquín Barrenechea, xg=0.05, shot_speed_kmh=87.6, outcome=goal, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=0.05, opponent_xg=0.0, team_shots=1, opponent_shots=0, assist=Jae-won Seo, assist_difficulty=7.6, player_goals=1, momentum=36

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-none-000057` | 03:18 | pass | Lorenzo Fabbrini-Neri | NOR | 39.0, 28.3 |
| `demo-none-000058` | 03:25 | pass | Ravi Khatri-Sen | NOR | 63.0, 17.7 |
| `demo-none-000059` | 03:32 | pass | Kyrylo Bondar | NOR | 38.0, 8.4 |
| `demo-none-000060` | 03:39 | pass | Nnamdi Okeke-Rhodes | NOR | 75.4, 48.0 |
| `demo-none-000061` | 03:43 | pass | Jae-won Seo | NOR | 58.8, 46.6 |
| `demo-none-000062` | 03:46 | shot | Joaquín Barrenechea | NOR | 89.2, 36.7 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Joaquín Barrenechea puts Northgate Rovers 0-1 ahead from just 0.05 xG; it was their only shot. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Joaquín Barrenechea ने 4वें मिनट में Northgate Rovers को 0-1 की बढ़त दिलाई। | 0.4 KB, 2 seg UCS-2 | model, verified |
| Fan roaming in Dubai | watch (ar) | هدف Joaquín Barrenechea! [0-1] | 0.53 KB | model, verified |

### 17:10 big_chance (`demo-none-mom-0003`)

Facts: minute=18, match_clock=17:10, score=0-1, team_code=NOR, player=Nnamdi Okeke-Rhodes, xg=0.3, shot_speed_kmh=92.7, outcome=saved, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=0.44, opponent_xg=0.0, team_shots=4, opponent_shots=0

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-none-000250` | 16:26 | tackle | Rafael Antunes Beira | RIV | 15.3, 60.5 |
| `demo-none-000251` | 16:26 | foul | Rafael Antunes Beira | RIV | 15.3, 60.5 |
| `demo-none-000252` | 16:42 | pass | Ravi Khatri-Sen | NOR | 89.7, 7.5 |
| `demo-none-000253` | 16:48 | shot | Nnamdi Okeke-Rhodes | NOR | 91.8, 45.9 |
| `demo-none-000254` | 17:09 | pass | Jae-won Seo | NOR | 104.5, 67.5 |
| `demo-none-000255` | 17:10 | shot | Nnamdi Okeke-Rhodes | NOR | 96.7, 36.0 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Northgate lead Riverside 1-0, but Nnamdi Okeke-Rhodes’s 0.3 xG effort was saved. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | 0-1: Nnamdi Okeke-Rhodes का शॉट बचा (18') | 0.2 KB, 1 seg UCS-2 | model, verified |
| Fan roaming in Dubai | watch (ar) | تصدى لتسديدة Nnamdi Okeke-Rhodes [0-1] | 0.54 KB | model, verified |

### 19:04 momentum_swing (`demo-none-mom-0004`)

Facts: minute=20, match_clock=19:04, score=0-1, team_code=NOR, momentum_now=64, momentum_5min_ago=12, swing=76, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=0.44, opponent_xg=0.0, team_shots=4, opponent_shots=0

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-none-000282` | 18:36 | pass | Mateus Brandão Lyra | NOR | 66.1, 65.7 |
| `demo-none-000283` | 18:39 | pass | Joaquín Barrenechea | NOR | 72.7, 44.2 |
| `demo-none-000284` | 18:46 | pass | Lorenzo Fabbrini-Neri | NOR | 52.3, 30.2 |
| `demo-none-000285` | 18:52 | carry | Kyrylo Bondar | NOR | 37.2, 9.0 |
| `demo-none-000286` | 18:55 | pass | Kyrylo Bondar | NOR | 53.1, 3.8 |
| `demo-none-000287` | 19:04 | carry | Ravi Khatri-Sen | NOR | 77.8, 6.0 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Northgate Rovers lead Riverside Athletic 0-1, with momentum surging from 12 to 64 after 4 shots and 0.44 xG. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | 0-1: Nnamdi Okeke-Rhodes का शॉट बचा (18') | 0.2 KB, 1 seg UCS-2 | model, verified |

### 47:00 half_time (`demo-none-mom-0006`)

Facts: minute=48, match_clock=47:00, score=0-1, home_xg=0.04, away_xg=0.44, home_shots=2, away_shots=5, home_possession=63, away_possession=37, home_pass_accuracy=90, away_pass_accuracy=90, top_performer=Joaquín Barrenechea, goals=[{'minute': 4, 'player': 'Joaquín Barrenechea', 'team': 'Northgate Rovers'}]

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-none-000724` | 46:41 | interception | Emeka Obiora-Lane | NOR | 18.6, 32.5 |
| `demo-none-000725` | 46:41 | possession_change | Emeka Obiora-Lane | NOR | 18.6, 32.5 |
| `demo-none-000726` | 46:46 | pass | Emeka Obiora-Lane | NOR | 18.6, 32.5 |
| `demo-none-000727` | 46:51 | pass | Kyrylo Bondar | NOR | 10.7, 13.3 |
| `demo-none-000728` | 46:57 | pass | Piet van Rossenberg | NOR | 5.2, 22.7 |
| `demo-none-000729` | 47:00 | half_time |  |  |  |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | At halftime, Northgate Rovers lead Riverside Athletic 0-1. Joaquín Barrenechea’s goal has put Riverside’s 0.04 xG into sharp relief: possession has brought little threat. | not budgeted | model, verified |
| Commuter, Jakarta | sms (id) | Riverside Athletic tertinggal 0-1 saat jeda, gol Joaquín Barrenechea. | 0.2 KB, 1 seg UCS-2 | model, verified |
| Student, Delhi | sms (hi) | ब्रेक: Riverside Athletic 0-1 Northgate Rovers। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 48:08 momentum_swing (`demo-none-mom-0007`)

Facts: minute=49, match_clock=48:08, score=0-1, team_code=NOR, momentum_now=36, momentum_5min_ago=8, swing=44, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=0.53, opponent_xg=0.04, team_shots=7, opponent_shots=2

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-none-000768` | 47:31 | pass | Ravi Khatri-Sen | NOR | 86.4, 53.7 |
| `demo-none-000769` | 47:35 | pass | Lorenzo Fabbrini-Neri | NOR | 70.6, 51.3 |
| `demo-none-000770` | 47:43 | pass | Kyrylo Bondar | NOR | 49.7, 59.6 |
| `demo-none-000771` | 47:51 | pass | Ravi Khatri-Sen | NOR | 79.4, 61.6 |
| `demo-none-000772` | 47:52 | shot | Joaquín Barrenechea | NOR | 91.5, 40.5 |
| `demo-none-000773` | 48:08 | possession_change | Mikael Brandvold | RIV | 5.5, 34.0 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | At 0-1, Northgate Rovers have surged from 8 to 36 in momentum, with a 7-2 shot advantage and a 0.53-0.04 expected-goals edge. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Northgate Rovers आगे, स्कोर 0-1। Riverside Athletic जवाब दे! | 0.2 KB, 1 seg UCS-2 | model, verified |

### 61:26 goal (`demo-none-mom-0008`)

Facts: minute=62, match_clock=61:26, score=0-2, team_code=NOR, player=Ravi Khatri-Sen, xg=0.65, shot_speed_kmh=111.4, outcome=goal, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=1.34, opponent_xg=0.04, team_shots=10, opponent_shots=2, assist=Joaquín Barrenechea, assist_difficulty=4.0, player_goals=1, momentum=-12

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-none-000970` | 61:09 | pass | Emeka Obiora-Lane | NOR | 38.8, 26.2 |
| `demo-none-000971` | 61:12 | pass | Nnamdi Okeke-Rhodes | NOR | 77.4, 9.3 |
| `demo-none-000972` | 61:16 | pressure | Hiroki Tanabe-Ross | RIV | 22.1, 39.4 |
| `demo-none-000973` | 61:18 | pass | Joaquín Barrenechea | NOR | 83.6, 28.3 |
| `demo-none-000974` | 61:24 | carry | Ravi Khatri-Sen | NOR | 90.5, 50.7 |
| `demo-none-000975` | 61:26 | shot | Ravi Khatri-Sen | NOR | 102.3, 37.2 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Ravi Khatri-Sen scores in the 62nd minute to put Northgate Rovers 2-0 ahead. | not budgeted | model, verified |
| Fan roaming in Dubai | watch (ar) | هدف Ravi Khatri-Sen لـ Northgate [0-2] | 0.54 KB | model, verified |
| Student, Delhi | sms (hi) | Ravi Khatri-Sen के गोल से Northgate Rovers ने 0-2 की बढ़त बनाई। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 68:04 momentum_swing (`demo-none-mom-0011`)

Facts: minute=69, match_clock=68:04, score=0-2, team_code=RIV, momentum_now=28, momentum_5min_ago=16, swing=44, team=Riverside Athletic, opponent=Northgate Rovers, team_xg=0.1, opponent_xg=1.34, team_shots=3, opponent_shots=10

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-none-001059` | 67:41 | foul | Rafael Antunes Beira | RIV | 26.2, 22.3 |
| `demo-none-001060` | 67:53 | carry | Lorenzo Fabbrini-Neri | NOR | 78.8, 45.7 |
| `demo-none-001061` | 67:54 | tackle | Yusuf Karadağlı | RIV | 11.6, 27.1 |
| `demo-none-001062` | 67:54 | possession_change | Yusuf Karadağlı | RIV | 10.5, 26.7 |
| `demo-none-001063` | 67:56 | pass | Yusuf Karadağlı | RIV | 13.2, 28.0 |
| `demo-none-001064` | 68:04 | tackle | Lorenzo Fabbrini-Neri | NOR | 75.6, 43.2 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Riverside Athletic’s momentum has climbed to 28, but they still trail Northgate Rovers 0-2. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Riverside Athletic की लय सुधरी, पर Northgate Rovers से 0-2 पीछे। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 72:06 goal (`demo-none-mom-0013`)

Facts: minute=73, match_clock=72:06, score=1-2, team_code=RIV, player=Kalani Akana, xg=0.11, shot_speed_kmh=109.9, outcome=goal, team=Riverside Athletic, opponent=Northgate Rovers, team_xg=0.21, opponent_xg=1.4, team_shots=4, opponent_shots=11, assist=Seamus Corrigan-Doyle, assist_difficulty=9.3, player_goals=1, momentum=24

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-none-001115` | 71:45 | pass | Dmytro Lysenko-Vale | RIV | 74.2, 37.8 |
| `demo-none-001116` | 71:51 | pass | Matteo Calvisano | RIV | 61.7, 23.3 |
| `demo-none-001117` | 71:54 | pressure | Nnamdi Okeke-Rhodes | NOR | 43.7, 21.1 |
| `demo-none-001118` | 71:56 | pass | Seamus Corrigan-Doyle | RIV | 62.2, 46.9 |
| `demo-none-001119` | 72:03 | carry | Kalani Akana | RIV | 87.0, 13.5 |
| `demo-none-001120` | 72:06 | shot | Kalani Akana | RIV | 103.4, 24.1 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Kalani Akana pulls Riverside Athletic within one at 1-2, finishing a chance worth just 0.11 xG. | not budgeted | model, verified |
| Fan roaming in Dubai | watch (ar) | Kalani Akana يقلّص الفارق [1-2] | 0.54 KB | model, verified |
| Commuter, Jakarta | sms (id) | Kalani Akana mencetak gol! Riverside Athletic kini tertinggal 1-2 dari Northgate Rovers. | 0.2 KB, 1 seg GSM-7 | model, verified |
| Student, Delhi | sms (hi) | Kalani Akana ने गोल किया; Riverside Athletic अब 1-2 से पीछे है। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 87:03 momentum_swing (`demo-none-mom-0015`)

Facts: minute=88, match_clock=87:03, score=1-2, team_code=NOR, momentum_now=56, momentum_5min_ago=20, swing=76, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=1.49, opponent_xg=0.39, team_shots=14, opponent_shots=7

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-none-001304` | 86:42 | carry | Emeka Obiora-Lane | NOR | 79.4, 36.5 |
| `demo-none-001305` | 86:46 | pass | Emeka Obiora-Lane | NOR | 93.0, 34.4 |
| `demo-none-001306` | 86:48 | pressure | Bastien Morvan | RIV | 33.6, 46.2 |
| `demo-none-001307` | 86:51 | pass | Callum Fairbairn | NOR | 72.5, 21.9 |
| `demo-none-001308` | 86:59 | pass | Nnamdi Okeke-Rhodes | NOR | 91.3, 8.9 |
| `demo-none-001309` | 87:03 | pass | Ravi Khatri-Sen | NOR | 89.0, 47.0 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Northgate Rovers lead Riverside Athletic 2-1, with momentum at 56 after a late surge. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | 1-2 पर Northgate Rovers ने रफ्तार पकड़ी; Riverside Athletic पर दबाव। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 93:00 full_time (`demo-none-mom-0016`)

Facts: minute=94, match_clock=93:00, score=1-2, home_xg=0.39, away_xg=1.49, home_shots=7, away_shots=14, home_possession=58, away_possession=42, home_pass_accuracy=90, away_pass_accuracy=89, top_performer=Ravi Khatri-Sen, goals=[{'minute': 4, 'player': 'Joaquín Barrenechea', 'team': 'Northgate Rovers'}, {'minute': 62, 'player': 'Ravi Khatri-Sen', 'team': 'Northgate Rovers'}, {'minute': 73, 'player': 'Kalani Akana', 'team': 'Riverside Athletic'}]

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-none-001397` | 92:25 | carry | Iñigo Larrazabal | RIV | 20.7, 62.6 |
| `demo-none-001398` | 92:30 | pass | Iñigo Larrazabal | RIV | 30.7, 63.8 |
| `demo-none-001399` | 92:50 | possession_change | Ravi Khatri-Sen | NOR | 87.6, 67.7 |
| `demo-none-001400` | 92:53 | carry | Ravi Khatri-Sen | NOR | 87.6, 67.7 |
| `demo-none-001401` | 92:57 | pass | Ravi Khatri-Sen | NOR | 101.1, 50.6 |
| `demo-none-001402` | 93:00 | full_time |  |  |  |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Northgate Rovers beat Riverside Athletic 2-1. Ravi Khatri-Sen’s 62nd-minute goal proved decisive, as Northgate outshot Riverside 14-7 despite the hosts’ 58% possession. | not budgeted | model, verified |
| Fan roaming in Dubai | watch (ar) | نورثغيت يفوز، وخاتري-سين نجم اللقاء [1-2] | 0.57 KB | model, verified |
| Student, Delhi | sms (hi) | Northgate Rovers ने Riverside Athletic को 1-2 से हराया। Ravi Khatri-Sen शीर्ष खिलाड़ी रहे। | 0.4 KB, 2 seg UCS-2 | model, verified |
| Commuter, Jakarta | sms (id) | Northgate Rovers menang 2-1 di kandang Riverside Athletic. Ravi Khatri-Sen jadi pemain terbaik; xG Northgate 1.49. | 0.2 KB, 1 seg GSM-7 | model, verified |

## Full-time digests

| Fan | Text | Size |
|---|---|---|
| Fan roaming in Dubai | نورثغيت يفوز، وخاتري-سين نجم اللقاء | 0.57 KB |
| Student, Delhi | Northgate Rovers ने Riverside Athletic को 1-2 से हराया। Ravi Khatri-Sen शीर्ष खिलाड़ी रहे। | 0.4 KB |
| Commuter, Jakarta | Northgate Rovers menang 2-1 di kandang Riverside Athletic. Ravi Khatri-Sen jadi pemain terbaik; xG Northgate 1.49. | 0.2 KB |
