# comeback: Riverside Athletic 2-3 Northgate Rovers

Seed 42, model `openai-compatible:gpt-6-luna`, recorded 2026-10-26 04:21 UTC.
Synthetic match, fictional clubs and players.

1334 events, 26 moments, 60 deliveries to 6 fans.

## Grounding check (the Verifier)

| Result | Count |
|---|---|
| Verifier passed | 60 |
| Verifier rejected, sent back to the Compressor | 1 |
| Fell back to a template after rejections | 0 |
| Deliveries written by the model (and verified) | 60 |
| Deliveries from a fallback template | 0 |

Template fallbacks by agent: explainer 1.

## Moments and their source events

### 02:31 goal (`demo-comeback-mom-0002`)

Facts: minute=3, match_clock=02:31, score=1-0, team_code=RIV, player=Kalani Akana, xg=0.93, shot_speed_kmh=87.4, outcome=goal, team=Riverside Athletic, opponent=Northgate Rovers, team_xg=0.94, opponent_xg=0.0, team_shots=2, opponent_shots=0, player_goals=1, momentum=36

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-comeback-000028` | 02:10 | possession_change | Kalani Akana | RIV | 74.0, 44.5 |
| `demo-comeback-000029` | 02:11 | tackle | Lorenzo Fabbrini-Neri | NOR | 31.0, 23.5 |
| `demo-comeback-000030` | 02:11 | foul | Lorenzo Fabbrini-Neri | NOR | 31.0, 23.5 |
| `demo-comeback-000031` | 02:25 | carry | Kalani Akana | RIV | 74.0, 44.5 |
| `demo-comeback-000032` | 02:29 | carry | Kalani Akana | RIV | 86.9, 32.1 |
| `demo-comeback-000033` | 02:31 | shot | Kalani Akana | RIV | 104.8, 31.2 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Kalani Akana scores to put Riverside Athletic 1-0 ahead of Northgate Rovers. | not budgeted | model, verified |
| Fan roaming in Dubai | watch (ar) | هدف! Kalani Akana يفتتح التسجيل [1-0] | 0.55 KB | model, verified |
| Student, Delhi | sms (hi) | Kalani Akana के गोल से Riverside Athletic ने 1-0 की बढ़त ली। | 0.2 KB, 1 seg UCS-2 | model, verified |
| Commuter, Jakarta | sms (id) | Gol Kalani Akana! Riverside Athletic unggul 1-0 atas Northgate Rovers. Awal yang kuat, laga masih panjang. | 0.2 KB, 1 seg GSM-7 | model, verified |

### 05:34 goal (`demo-comeback-mom-0003`)

Facts: minute=6, match_clock=05:34, score=2-0, team_code=RIV, player=Thiago Esquível, xg=0.26, shot_speed_kmh=103.3, outcome=goal, team=Riverside Athletic, opponent=Northgate Rovers, team_xg=1.2, opponent_xg=0.0, team_shots=3, opponent_shots=0, assist=Matteo Calvisano, assist_difficulty=7.0, player_goals=1, momentum=60

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-comeback-000056` | 05:12 | pass | Lukas Brenneisen | RIV | 29.5, 41.4 |
| `demo-comeback-000057` | 05:18 | pass | Matteo Calvisano | RIV | 42.9, 47.2 |
| `demo-comeback-000058` | 05:25 | carry | Thiago Esquível | RIV | 73.9, 17.9 |
| `demo-comeback-000059` | 05:28 | carry | Thiago Esquível | RIV | 84.7, 26.8 |
| `demo-comeback-000060` | 05:31 | carry | Thiago Esquível | RIV | 98.1, 31.5 |
| `demo-comeback-000061` | 05:34 | shot | Thiago Esquível | RIV | 104.8, 38.2 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Thiago Esquível scores in the 6th minute to put Riverside Athletic 2-0 ahead. | not budgeted | model, verified |
| Fan roaming in Dubai | watch (ar) | هدف Thiago Esquível يعزز تقدم ريفرسايد [2-0] | 0.56 KB | model, verified |
| Commuter, Jakarta | sms (id) | Thiago Esquivel mencetak gol menit 6, membawa Riverside Athletic unggul 2-0 atas Northgate Rovers. | 0.2 KB, 1 seg GSM-7 | model, verified |
| Student, Delhi | sms (hi) | Thiago Esquível के गोल से Riverside Athletic 2-0 से आगे। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 11:24 big_chance (`demo-comeback-mom-0006`)

Facts: minute=12, match_clock=11:24, score=2-0, team_code=NOR, player=Ravi Khatri-Sen, xg=0.34, shot_speed_kmh=98.2, outcome=saved, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=0.43, opponent_xg=1.2, team_shots=3, opponent_shots=3

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-comeback-000130` | 11:14 | shot | Nnamdi Okeke-Rhodes | NOR | 96.0, 42.3 |
| `demo-comeback-000131` | 11:14 | possession_change | Mikael Brandvold | RIV | 1.0, 31.4 |
| `demo-comeback-000132` | 11:21 | pass | Mikael Brandvold | RIV | 1.0, 31.4 |
| `demo-comeback-000133` | 11:21 | interception | Ravi Khatri-Sen | NOR | 99.0, 32.9 |
| `demo-comeback-000134` | 11:21 | possession_change | Ravi Khatri-Sen | NOR | 99.1, 33.6 |
| `demo-comeback-000135` | 11:24 | shot | Ravi Khatri-Sen | NOR | 99.1, 33.6 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Ravi Khatri-Sen’s chance was saved as Northgate Rovers trailed Riverside Athletic 2-0. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | 2-0 पर Ravi Khatri-Sen का शॉट Riverside Athletic ने बचाया। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 12:03 momentum_swing (`demo-comeback-mom-0007`)

Facts: minute=13, match_clock=12:03, score=2-0, team_code=NOR, momentum_now=64, momentum_5min_ago=40, swing=104, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=0.43, opponent_xg=1.2, team_shots=3, opponent_shots=3

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-comeback-000135` | 11:24 | shot | Ravi Khatri-Sen | NOR | 99.1, 33.6 |
| `demo-comeback-000136` | 11:46 | pass | Ravi Khatri-Sen | NOR | 104.5, 0.5 |
| `demo-comeback-000137` | 11:49 | pass | Joaquín Barrenechea | NOR | 99.4, 35.9 |
| `demo-comeback-000138` | 11:52 | pass | Lorenzo Fabbrini-Neri | NOR | 88.3, 23.7 |
| `demo-comeback-000139` | 11:56 | pass | Jae-won Seo | NOR | 82.0, 45.0 |
| `demo-comeback-000140` | 12:03 | pass | Nnamdi Okeke-Rhodes | NOR | 93.1, 54.1 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Northgate Rovers' momentum has climbed to 64, but they trail Riverside Athletic 2-0. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | 2-0 पर Ravi Khatri-Sen का शॉट Riverside Athletic ने बचाया। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 15:46 big_chance (`demo-comeback-mom-0008`)

Facts: minute=16, match_clock=15:46, score=2-0, team_code=NOR, player=Nnamdi Okeke-Rhodes, xg=0.4, shot_speed_kmh=95.3, outcome=off_target, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=0.84, opponent_xg=1.2, team_shots=6, opponent_shots=3

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-comeback-000193` | 15:27 | pass | Joaquín Barrenechea | NOR | 86.6, 35.3 |
| `demo-comeback-000194` | 15:30 | pressure | Kalani Akana | RIV | 32.4, 45.3 |
| `demo-comeback-000195` | 15:33 | pass | Lorenzo Fabbrini-Neri | NOR | 73.4, 23.6 |
| `demo-comeback-000196` | 15:41 | carry | Nnamdi Okeke-Rhodes | NOR | 92.0, 52.8 |
| `demo-comeback-000197` | 15:43 | carry | Nnamdi Okeke-Rhodes | NOR | 104.8, 48.3 |
| `demo-comeback-000198` | 15:46 | shot | Nnamdi Okeke-Rhodes | NOR | 103.5, 38.7 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Nnamdi Okeke-Rhodes misses the target as Northgate Rovers trail Riverside Athletic 2-0, despite 0.84 xG. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Nnamdi Okeke-Rhodes का शॉट चूका; Northgate Rovers 2-0 से पीछे। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 27:04 momentum_swing (`demo-comeback-mom-0011`)

Facts: minute=28, match_clock=27:04, score=2-0, team_code=RIV, momentum_now=28, momentum_5min_ago=62, swing=90, team=Riverside Athletic, opponent=Northgate Rovers, team_xg=1.2, opponent_xg=1.31, team_shots=3, opponent_shots=9

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-comeback-000374` | 26:39 | tackle | Lorenzo Fabbrini-Neri | NOR | 54.5, 30.0 |
| `demo-comeback-000375` | 26:39 | foul | Lorenzo Fabbrini-Neri | NOR | 54.5, 30.0 |
| `demo-comeback-000376` | 26:49 | pass | Dmytro Lysenko-Vale | RIV | 50.5, 38.0 |
| `demo-comeback-000377` | 26:52 | pass | Matteo Calvisano | RIV | 53.8, 47.8 |
| `demo-comeback-000378` | 26:57 | pass | Hiroki Tanabe-Ross | RIV | 49.4, 37.6 |
| `demo-comeback-000379` | 27:04 | pass | Lukas Brenneisen | RIV | 32.6, 45.0 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Riverside Athletic lead 2-0, but Northgate Rovers are applying pressure as Riverside’s momentum falls to 28. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Riverside Athletic 2-0 से आगे, Northgate Rovers दबाव बना रहे हैं। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 27:39 big_chance (`demo-comeback-mom-0013`)

Facts: minute=28, match_clock=27:39, score=2-0, team_code=NOR, player=Ravi Khatri-Sen, xg=0.66, shot_speed_kmh=96.9, outcome=off_target, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=1.97, opponent_xg=1.2, team_shots=10, opponent_shots=3

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-comeback-000384` | 27:20 | pass | Joaquín Barrenechea | NOR | 62.0, 14.6 |
| `demo-comeback-000385` | 27:23 | pressure | Thiago Esquível | RIV | 49.7, 26.7 |
| `demo-comeback-000386` | 27:26 | pass | Jae-won Seo | NOR | 55.6, 40.6 |
| `demo-comeback-000387` | 27:33 | carry | Ravi Khatri-Sen | NOR | 85.6, 12.8 |
| `demo-comeback-000388` | 27:37 | carry | Ravi Khatri-Sen | NOR | 104.8, 20.3 |
| `demo-comeback-000389` | 27:39 | shot | Ravi Khatri-Sen | NOR | 103.6, 30.3 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | At 2-0, Northgate’s Ravi Khatri-Sen sends a 0.66 xG chance off target despite Northgate’s 10-3 shot advantage. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Ravi Khatri-Sen ने बड़ा मौका गंवाया; स्कोर 2-0। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 31:10 red_card (`demo-comeback-mom-0014`)

Facts: minute=32, match_clock=31:10, score=2-0, team_code=RIV, player=Dmytro Lysenko-Vale, team=Riverside Athletic, team_fouls=3, players_left=10

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-comeback-000440` | 30:56 | possession_change | Ravi Khatri-Sen | NOR | 16.7, 10.8 |
| `demo-comeback-000441` | 31:03 | carry | Ravi Khatri-Sen | NOR | 16.7, 10.8 |
| `demo-comeback-000442` | 31:07 | pass | Ravi Khatri-Sen | NOR | 31.0, 10.0 |
| `demo-comeback-000443` | 31:09 | pressure | Dmytro Lysenko-Vale | RIV | 94.1, 31.2 |
| `demo-comeback-000444` | 31:10 | tackle | Dmytro Lysenko-Vale | RIV | 94.8, 31.1 |
| `demo-comeback-000445` | 31:10 | foul | Dmytro Lysenko-Vale | RIV | 94.8, 31.1 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Riverside Athletic lead 2-0, but Dmytro Lysenko-Vale’s red card leaves them down to 10 against Northgate Rovers. | not budgeted | model, verified |
| Fan roaming in Dubai | watch (ar) | طرد Dmytro يترك ريفرسايد منقوصًا [10] | 0.55 KB | model, verified |
| Student, Delhi | sms (hi) | 2-0 पर RIV के Dmytro Lysenko-Vale को लाल कार्ड; 10 खिलाड़ी। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 37:06 momentum_swing (`demo-comeback-mom-0015`)

Facts: minute=38, match_clock=37:06, score=2-0, team_code=NOR, momentum_now=40, momentum_5min_ago=16, swing=56, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=1.98, opponent_xg=1.2, team_shots=11, opponent_shots=3

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-comeback-000520` | 36:27 | pass | Iñigo Larrazabal | RIV | 14.2, 7.9 |
| `demo-comeback-000521` | 36:32 | carry | Kwabena Darko-Mensah | RIV | 9.5, 22.1 |
| `demo-comeback-000522` | 36:35 | pass | Kwabena Darko-Mensah | RIV | 19.4, 19.8 |
| `demo-comeback-000523` | 36:43 | carry | Iñigo Larrazabal | RIV | 11.5, 9.5 |
| `demo-comeback-000524` | 36:48 | pass | Iñigo Larrazabal | RIV | 29.3, 3.6 |
| `demo-comeback-000525` | 37:06 | possession_change | Ravi Khatri-Sen | NOR | 68.7, 0.3 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Northgate Rovers trail Riverside Athletic 2-0, but their momentum has surged to 40. They have 11 shots and 1.98 xG, compared with Riverside’s 3 shots and 1.2 xG. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | RIV, 2-0 आगे; Northgate Rovers का दबाव बढ़ा। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 47:00 half_time (`demo-comeback-mom-0016`)

Facts: minute=48, match_clock=47:00, score=2-0, home_xg=1.2, away_xg=1.98, home_shots=3, away_shots=11, home_possession=54, away_possession=46, home_pass_accuracy=89, away_pass_accuracy=88, top_performer=Jae-won Seo, goals=[{'minute': 3, 'player': 'Kalani Akana', 'team': 'Riverside Athletic'}, {'minute': 6, 'player': 'Thiago Esquível', 'team': 'Riverside Athletic'}]

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-comeback-000664` | 46:38 | pass | Iñigo Larrazabal | RIV | 22.2, 15.8 |
| `demo-comeback-000665` | 46:43 | pass | Hiroki Tanabe-Ross | RIV | 31.1, 32.5 |
| `demo-comeback-000666` | 46:49 | pass | Kwabena Darko-Mensah | RIV | 20.1, 25.5 |
| `demo-comeback-000667` | 46:50 | tackle | Ravi Khatri-Sen | NOR | 70.0, 21.5 |
| `demo-comeback-000668` | 46:50 | foul | Ravi Khatri-Sen | NOR | 70.0, 21.5 |
| `demo-comeback-000669` | 47:00 | half_time |  |  |  |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Riverside Athletic lead Northgate Rovers 2-0 at halftime, but Northgate have the higher expected goals at 1.98. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Riverside Athletic 2-0 आगे; Kalani Akana, Thiago Esquível के गोल। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 58:01 momentum_swing (`demo-comeback-mom-0018`)

Facts: minute=59, match_clock=58:01, score=2-0, team_code=NOR, momentum_now=28, momentum_5min_ago=12, swing=40, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=2.0, opponent_xg=1.21, team_shots=12, opponent_shots=4

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-comeback-000841` | 57:30 | foul | Ravi Khatri-Sen | NOR | 66.8, 37.9 |
| `demo-comeback-000842` | 57:46 | pass | Hiroki Tanabe-Ross | RIV | 38.2, 30.1 |
| `demo-comeback-000843` | 57:47 | pressure | Ravi Khatri-Sen | NOR | 60.6, 49.1 |
| `demo-comeback-000844` | 57:49 | pass | Matteo Calvisano | RIV | 43.8, 18.9 |
| `demo-comeback-000845` | 57:58 | carry | Rafael Antunes Beira | RIV | 26.4, 7.4 |
| `demo-comeback-000846` | 58:01 | pass | Rafael Antunes Beira | RIV | 39.9, 7.1 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Northgate Rovers’ momentum has climbed from 12 to 28, but they trail Riverside Athletic 2-0 despite leading 12-4 in shots. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Riverside Athletic 2-0 आगे, पर Northgate Rovers का दबाव बढ़ा (40)। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 75:22 goal (`demo-comeback-mom-0022`)

Facts: minute=76, match_clock=75:22, score=2-1, team_code=NOR, player=Joaquín Barrenechea, xg=0.04, shot_speed_kmh=81.5, outcome=goal, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=2.23, opponent_xg=1.21, team_shots=14, opponent_shots=4, assist=Ravi Khatri-Sen, assist_difficulty=5.4, player_goals=1, momentum=32

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-comeback-001108` | 75:13 | pass | Seamus Corrigan-Doyle | RIV | 32.7, 19.3 |
| `demo-comeback-001109` | 75:13 | interception | Ravi Khatri-Sen | NOR | 75.7, 51.3 |
| `demo-comeback-001110` | 75:13 | possession_change | Ravi Khatri-Sen | NOR | 74.7, 50.7 |
| `demo-comeback-001111` | 75:17 | pass | Ravi Khatri-Sen | NOR | 74.7, 50.7 |
| `demo-comeback-001112` | 75:20 | pressure | Hiroki Tanabe-Ross | RIV | 18.1, 29.9 |
| `demo-comeback-001113` | 75:22 | shot | Joaquín Barrenechea | NOR | 87.8, 37.8 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Joaquín Barrenechea pulls Northgate back to 2-1 with a finish from a 0.04 xG chance. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Joaquín Barrenechea के गोल से Northgate Rovers ने जवाब दिया; Riverside Athletic अब भी 2-1 से आगे। | 0.4 KB, 2 seg UCS-2 | model, verified |
| Fan roaming in Dubai | watch (ar) | هدف لـ Joaquín Barrenechea [2-1] | 0.53 KB | model, verified |

### 77:01 momentum_swing (`demo-comeback-mom-0023`)

Facts: minute=78, match_clock=77:01, score=2-1, team_code=NOR, momentum_now=32, momentum_5min_ago=12, swing=44, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=2.23, opponent_xg=1.21, team_shots=14, opponent_shots=4

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-comeback-001124` | 76:50 | pass | Chidubem Nwachukwu-Bello | RIV | 34.8, 47.4 |
| `demo-comeback-001125` | 76:50 | interception | Nnamdi Okeke-Rhodes | NOR | 74.8, 29.2 |
| `demo-comeback-001126` | 76:50 | possession_change | Nnamdi Okeke-Rhodes | NOR | 71.0, 22.9 |
| `demo-comeback-001127` | 76:53 | pass | Nnamdi Okeke-Rhodes | NOR | 71.0, 22.9 |
| `demo-comeback-001128` | 76:59 | pressure | Hiroki Tanabe-Ross | RIV | 41.2, 35.6 |
| `demo-comeback-001129` | 77:01 | carry | Emeka Obiora-Lane | NOR | 53.3, 32.9 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Northgate Rovers have surged, but still trail Riverside Athletic 2-1 after 14 shots. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Northgate Rovers का दबाव, Riverside Athletic 2-1 से आगे; गति +44। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 81:49 goal (`demo-comeback-mom-0024`)

Facts: minute=82, match_clock=81:49, score=2-2, team_code=NOR, player=Nnamdi Okeke-Rhodes, xg=0.93, shot_speed_kmh=109.0, outcome=goal, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=3.16, opponent_xg=1.21, team_shots=15, opponent_shots=4, assist=Callum Fairbairn, assist_difficulty=6.2, player_goals=1, momentum=36

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-comeback-001198` | 81:24 | pass | Joaquín Barrenechea | NOR | 75.6, 34.7 |
| `demo-comeback-001199` | 81:32 | carry | Callum Fairbairn | NOR | 51.2, 24.5 |
| `demo-comeback-001200` | 81:35 | pass | Callum Fairbairn | NOR | 59.8, 18.3 |
| `demo-comeback-001201` | 81:43 | carry | Nnamdi Okeke-Rhodes | NOR | 84.7, 9.0 |
| `demo-comeback-001202` | 81:47 | carry | Nnamdi Okeke-Rhodes | NOR | 100.4, 24.0 |
| `demo-comeback-001203` | 81:49 | shot | Nnamdi Okeke-Rhodes | NOR | 104.8, 37.3 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Nnamdi Okeke-Rhodes’ 82nd-minute goal came from a 0.93 xG chance, as Northgate led the shot count 15-4 in a 2-2 match. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Nnamdi Okeke-Rhodes ने 82वें मिनट में गोल किया; स्कोर 2-2। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 84:02 goal (`demo-comeback-mom-0025`)

Facts: minute=85, match_clock=84:02, score=2-3, team_code=NOR, player=Nnamdi Okeke-Rhodes, xg=0.14, shot_speed_kmh=90.1, outcome=goal, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=3.3, opponent_xg=1.21, team_shots=16, opponent_shots=4, assist=Kyrylo Bondar, assist_difficulty=7.0, player_goals=2, momentum=60

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-comeback-001218` | 83:33 | pass | Callum Fairbairn | NOR | 50.7, 21.5 |
| `demo-comeback-001219` | 83:39 | pass | Emeka Obiora-Lane | NOR | 48.5, 28.8 |
| `demo-comeback-001220` | 83:47 | pass | Kyrylo Bondar | NOR | 28.6, 54.0 |
| `demo-comeback-001221` | 83:56 | carry | Nnamdi Okeke-Rhodes | NOR | 72.1, 16.0 |
| `demo-comeback-001222` | 84:00 | carry | Nnamdi Okeke-Rhodes | NOR | 89.0, 22.5 |
| `demo-comeback-001223` | 84:02 | shot | Nnamdi Okeke-Rhodes | NOR | 104.8, 27.5 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Nnamdi Okeke-Rhodes scores his second to put Northgate Rovers 3-2 ahead in the 85th minute. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | 85वें मिनट में Nnamdi Okeke-Rhodes के गोल से Northgate Rovers 2-3 से आगे! Riverside Athletic के लिए बड़ा झटका। | 0.4 KB, 2 seg UCS-2 | model, verified |

### 92:00 full_time (`demo-comeback-mom-0026`)

Facts: minute=93, match_clock=92:00, score=2-3, home_xg=1.21, away_xg=3.52, home_shots=4, away_shots=19, home_possession=51, away_possession=49, home_pass_accuracy=88, away_pass_accuracy=89, top_performer=Nnamdi Okeke-Rhodes, goals=[{'minute': 3, 'player': 'Kalani Akana', 'team': 'Riverside Athletic'}, {'minute': 6, 'player': 'Thiago Esquível', 'team': 'Riverside Athletic'}, {'minute': 76, 'player': 'Joaquín Barrenechea', 'team': 'Northgate Rovers'}, {'minute': 82, 'player': 'Nnamdi Okeke-Rhodes', 'team': 'Northgate Rovers'}, {'minute': 85, 'player': 'Nnamdi Okeke-Rhodes', 'team': 'Northgate Rovers'}]

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-comeback-001329` | 91:44 | pass | Yusuf Karadağlı | RIV | 2.8, 57.7 |
| `demo-comeback-001330` | 91:48 | pass | Bastien Morvan | RIV | 50.0, 61.5 |
| `demo-comeback-001331` | 91:48 | interception | Callum Fairbairn | NOR | 58.5, 14.6 |
| `demo-comeback-001332` | 91:48 | possession_change | Callum Fairbairn | NOR | 56.7, 12.0 |
| `demo-comeback-001333` | 91:53 | pass | Callum Fairbairn | NOR | 56.7, 12.0 |
| `demo-comeback-001334` | 92:00 | full_time |  |  |  |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Northgate Rovers came from 2-0 down to beat Riverside Athletic 3-2. Nnamdi Okeke-Rhodes scored twice, and Northgate finished with 19 shots. | not budgeted | model, verified |
| Fan roaming in Dubai | watch (ar) | عودة نورثغيت بقيادة أوكيكي-رودز [2-3] | 0.56 KB | model, verified |
| Commuter, Jakarta | sms (id) | Riverside Athletic 2-3 Northgate Rovers! Nnamdi Okeke-Rhodes jadi bintang, mencetak 2 gol dalam comeback dramatis. | 0.2 KB, 1 seg GSM-7 | model, verified |
| Student, Delhi | sms (hi) | Northgate Rovers ने Riverside Athletic को 2-3 से हराया। Nnamdi Okeke-Rhodes के 82वें और 85वें मिनट के गोल निर्णायक रहे। | 0.4 KB, 2 seg UCS-2 | model, verified |

## Full-time digests

| Fan | Text | Size |
|---|---|---|
| Fan, Lagos | Northgate Rovers beat Riverside Athletic 3-2 after coming back from 2 goals down, as Nnamdi Okeke-Rhodes score twice. | 14.6 KB |
| Office worker, São Paulo | Nnamdi Okeke-Rhodes fez 2 gols na virada do Northgate Rovers sobre o Riverside Athletic, por 3 a 2. | 1.13 KB |
| Fan roaming in Dubai | عودة نورثغيت بقيادة أوكيكي-رودز | 0.56 KB |
| Commuter, Jakarta | Riverside Athletic 2-3 Northgate Rovers! Nnamdi Okeke-Rhodes jadi bintang, mencetak 2 gol dalam comeback dramatis. | 0.2 KB |
| Student, Delhi | Northgate Rovers ने Riverside Athletic को 2-3 से हराया। Nnamdi Okeke-Rhodes के 82वें और 85वें मिनट के गोल निर्णायक रहे। | 0.4 KB |
