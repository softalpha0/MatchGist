# comeback: Riverside Athletic 2-3 Northgate Rovers

Seed 42, model `offline-templates`, recorded 2026-10-26 03:47 UTC.
Synthetic match, fictional clubs and players.

1334 events, 26 moments, 60 deliveries to 6 fans.

## Grounding check (the Verifier)

| Result | Count |
|---|---|
| Verifier passed | 60 |
| Verifier rejected, sent back to the Compressor | 7 |
| Fell back to a template after rejections | 0 |
| Deliveries written by the offline templates (and verified) | 60 |
| Deliveries from a fallback template | 0 |

Template fallbacks by agent: none.

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
| Studio analyst, London | broadcast (en) | Kalani Akana scores for Riverside Athletic (3'): RIV 1-0 NOR. A 0.93 xG chance, struck at 87.4 km/h. | not budgeted | offline templates, verified |
| Commuter, Jakarta | sms (id) | Kalani Akana mencetak gol untuk Riverside Athletic (3'): RIV 1-0 NOR. | 0.2 KB, 1 seg GSM-7 | offline templates, verified |
| Student, Delhi | sms (hi) | Riverside Athletic के लिए Kalani Akana का गोल (3'): RIV 1-0 NOR। | 0.2 KB, 1 seg UCS-2 | offline templates, verified |
| Fan roaming in Dubai | watch (ar) | هدف RIV ⁨Akana⁩ [1-0] | 0.52 KB | offline templates, verified |

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
| Studio analyst, London | broadcast (en) | Thiago Esquível scores for Riverside Athletic (6'): RIV 2-0 NOR. A 0.26 xG chance, struck at 103.3 km/h. | not budgeted | offline templates, verified |
| Commuter, Jakarta | sms (id) | Thiago Esquivel mencetak gol untuk Riverside Athletic (6'): RIV 2-0 NOR. | 0.2 KB, 1 seg GSM-7 | offline templates, verified |
| Student, Delhi | sms (hi) | Riverside Athletic के लिए Thiago Esquível का गोल (6'): RIV 2-0 NOR। | 0.2 KB, 1 seg UCS-2 | offline templates, verified |
| Fan roaming in Dubai | watch (ar) | هدف RIV ⁨Esquível⁩ [2-0] | 0.53 KB | offline templates, verified |

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
| Studio analyst, London | broadcast (en) | Ravi Khatri-Sen should have scored (12'): a 0.34 xG chance, saved. Still RIV 2-0 NOR. | not budgeted | offline templates, verified |
| Student, Delhi | sms (hi) | को गोल करना चाहिए था ('): xG का मौका, । | 0.2 KB, 1 seg UCS-2 | offline templates, verified |

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
| Studio analyst, London | broadcast (en) | The game has turned: Northgate Rovers now hold the momentum (13'), 3 shots to 3. | not budgeted | offline templates, verified |
| Student, Delhi | sms (hi) | को गोल करना चाहिए था ('): xG का मौका, । | 0.2 KB, 1 seg UCS-2 | offline templates, verified |

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
| Studio analyst, London | broadcast (en) | Nnamdi Okeke-Rhodes should have scored (16'): a 0.4 xG chance, off target. Still RIV 2-0 NOR. | not budgeted | offline templates, verified |
| Student, Delhi | sms (hi) | बड़ा मौका NOR (16') Nnamdi Okeke-Rhodes | 0.2 KB, 1 seg UCS-2 | offline templates, verified |

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
| Studio analyst, London | broadcast (en) | The game has turned: Riverside Athletic now hold the momentum (28'), 3 shots to 9. | not budgeted | offline templates, verified |
| Student, Delhi | sms (hi) | खेल पलट गया: अब Riverside Athletic का दबदबा है (28'), शॉट 3 बनाम 9। | 0.2 KB, 1 seg UCS-2 | offline templates, verified |

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
| Studio analyst, London | broadcast (en) | Ravi Khatri-Sen should have scored (28'): a 0.66 xG chance, off target. Still RIV 2-0 NOR. | not budgeted | offline templates, verified |
| Student, Delhi | sms (hi) | बड़ा मौका NOR (28') Ravi Khatri-Sen | 0.2 KB, 1 seg UCS-2 | offline templates, verified |

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
| Studio analyst, London | broadcast (en) | Dmytro Lysenko-Vale is sent off (32'). Riverside Athletic are down to 10 at RIV 2-0 NOR. | not budgeted | offline templates, verified |
| Student, Delhi | sms (hi) | Dmytro Lysenko-Vale को बाहर भेजा गया (32')। | 0.2 KB, 1 seg UCS-2 | offline templates, verified |
| Fan roaming in Dubai | watch (ar) | بطاقة حمراء ⁨Lysenko-Vale⁩ [2-0] | 0.54 KB | offline templates, verified |

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
| Studio analyst, London | broadcast (en) | The game has turned: Northgate Rovers now hold the momentum (38'), 11 shots to 3. | not budgeted | offline templates, verified |
| Student, Delhi | sms (hi) | खेल पलट गया: अब Northgate Rovers का दबदबा है (38'), शॉट 11 बनाम 3। | 0.2 KB, 1 seg UCS-2 | offline templates, verified |

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
| Studio analyst, London | broadcast (en) | Half-time: Riverside Athletic 2-0 Northgate Rovers. xG 1.2 to 1.98, possession 54% to 46%. | not budgeted | offline templates, verified |
| Student, Delhi | sms (hi) | हाफ टाइम: Riverside Athletic 2-0 Northgate Rovers। | 0.2 KB, 1 seg UCS-2 | offline templates, verified |

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
| Studio analyst, London | broadcast (en) | The game has turned: Northgate Rovers now hold the momentum (59'), 12 shots to 4. | not budgeted | offline templates, verified |
| Student, Delhi | sms (hi) | खेल पलट गया: अब Northgate Rovers का दबदबा है (59'), शॉट 12 बनाम 4। | 0.2 KB, 1 seg UCS-2 | offline templates, verified |

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
| Studio analyst, London | broadcast (en) | Joaquín Barrenechea scores for Northgate Rovers (76'): RIV 2-1 NOR. A 0.04 xG chance, struck at 81.5 km/h. | not budgeted | offline templates, verified |
| Student, Delhi | sms (hi) | Northgate Rovers के लिए Joaquín Barrenechea का गोल (76'): RIV 2-1 NOR। | 0.2 KB, 1 seg UCS-2 | offline templates, verified |
| Fan roaming in Dubai | watch (ar) | هدف NOR ⁨Barrenechea⁩ [2-1] | 0.53 KB | offline templates, verified |

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
| Studio analyst, London | broadcast (en) | The game has turned: Northgate Rovers now hold the momentum (78'), 14 shots to 4. | not budgeted | offline templates, verified |
| Student, Delhi | sms (hi) | खेल पलट गया: अब Northgate Rovers का दबदबा है (78'), शॉट 14 बनाम 4। | 0.2 KB, 1 seg UCS-2 | offline templates, verified |

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
| Studio analyst, London | broadcast (en) | Nnamdi Okeke-Rhodes scores for Northgate Rovers (82'): RIV 2-2 NOR. A 0.93 xG chance, struck at 109.0 km/h. | not budgeted | offline templates, verified |
| Student, Delhi | sms (hi) | Northgate Rovers के लिए Nnamdi Okeke-Rhodes का गोल (82'): RIV 2-2 NOR। | 0.2 KB, 1 seg UCS-2 | offline templates, verified |

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
| Studio analyst, London | broadcast (en) | Nnamdi Okeke-Rhodes scores for Northgate Rovers (85'): RIV 2-3 NOR. A 0.14 xG chance, struck at 90.1 km/h. | not budgeted | offline templates, verified |
| Student, Delhi | sms (hi) | Northgate Rovers के लिए Nnamdi Okeke-Rhodes का गोल (85'): RIV 2-3 NOR। | 0.2 KB, 1 seg UCS-2 | offline templates, verified |

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
| Commuter, Jakarta | sms (id) | Laga usai: Riverside Athletic 2-3 Northgate Rovers. Akana 3', Esquivel 6', Barrenechea 76', Okeke-Rhodes 82', Okeke-Rhodes 85' | 0.2 KB, 1 seg GSM-7 | offline templates, verified |
| Student, Delhi | sms (hi) | मैच खत्म: Riverside Athletic 2-3 Northgate Rovers। Akana 3', Esquível 6', Barrenechea 76', Okeke-Rhodes 82', Okeke-Rhodes 85' | 0.4 KB, 2 seg UCS-2 | offline templates, verified |
| Fan roaming in Dubai | watch (ar) | نهاية المباراة [2-3] | 0.53 KB | offline templates, verified |
| Studio analyst, London | broadcast (en) | Full-time: Riverside Athletic 2-3 Northgate Rovers. xG 1.21 to 3.52. Player of the match: Nnamdi Okeke-Rhodes. | not budgeted | offline templates, verified |

## Full-time digests

| Fan | Text | Size |
|---|---|---|
| Commuter, Jakarta | Laga usai: Riverside Athletic 2-3 Northgate Rovers. Akana 3', Esquivel 6', Barrenechea 76', Okeke-Rhodes 82', Okeke-Rhodes 85' | 0.2 KB |
| Fan, Lagos | Match don end: Riverside Athletic 2-3 Northgate Rovers. Akana 3', Esquível 6', Barrenechea 76', Okeke-Rhodes 82', Okeke-Rhodes 85' | 14.6 KB |
| Office worker, São Paulo | Fim de jogo: Riverside Athletic 2-3 Northgate Rovers. | 1.07 KB |
| Student, Delhi | मैच खत्म: Riverside Athletic 2-3 Northgate Rovers। Akana 3', Esquível 6', Barrenechea 76', Okeke-Rhodes 82', Okeke-Rhodes 85' | 0.4 KB |
| Fan roaming in Dubai | نهاية المباراة | 0.53 KB |
