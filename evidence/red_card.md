# red_card: Riverside Athletic 4-2 Northgate Rovers

Seed 42, model `openai-compatible:gpt-6-luna`, recorded 2026-10-26 04:25 UTC.
Synthetic match, fictional clubs and players.

1422 events, 15 moments, 43 deliveries to 6 fans.

## Grounding check (the Verifier)

| Result | Count |
|---|---|
| Verifier passed | 43 |
| Verifier rejected, sent back to the Compressor | 1 |
| Fell back to a template after rejections | 0 |
| Deliveries written by the model (and verified) | 43 |
| Deliveries from a fallback template | 0 |

Template fallbacks by agent: explainer 2.

## Moments and their source events

### 16:14 goal (`demo-red_card-mom-0001`)

Facts: minute=17, match_clock=16:14, score=0-1, team_code=NOR, player=Nnamdi Okeke-Rhodes, xg=0.49, shot_speed_kmh=104.4, outcome=goal, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=0.78, opponent_xg=0.0, team_shots=5, opponent_shots=0, assist=Ravi Khatri-Sen, assist_difficulty=2.3, player_goals=1, momentum=60

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-red_card-000232` | 15:43 | pressure | Nnamdi Okeke-Rhodes | NOR | 97.5, 57.2 |
| `demo-red_card-000233` | 15:45 | pass | Iñigo Larrazabal | RIV | 6.5, 10.3 |
| `demo-red_card-000234` | 16:05 | possession_change | Nnamdi Okeke-Rhodes | NOR | 81.4, 67.7 |
| `demo-red_card-000235` | 16:09 | carry | Nnamdi Okeke-Rhodes | NOR | 81.4, 67.7 |
| `demo-red_card-000236` | 16:13 | carry | Nnamdi Okeke-Rhodes | NOR | 88.4, 47.5 |
| `demo-red_card-000237` | 16:14 | shot | Nnamdi Okeke-Rhodes | NOR | 100.6, 33.5 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Nnamdi Okeke-Rhodes scores in the 17th minute to put Northgate Rovers 1-0 ahead. | not budgeted | model, verified |
| Fan roaming in Dubai | watch (ar) | هدف Nnamdi Okeke-Rhodes! [0-1] | 0.53 KB | model, verified |
| Student, Delhi | sms (hi) | Nnamdi Okeke-Rhodes के गोल से Northgate Rovers 0-1 से आगे है। गोल 17वें मिनट में हुआ। | 0.4 KB, 2 seg UCS-2 | model, verified |

### 38:30 goal (`demo-red_card-mom-0003`)

Facts: minute=39, match_clock=38:30, score=1-1, team_code=RIV, player=Dmytro Lysenko-Vale, xg=0.23, shot_speed_kmh=99.7, outcome=goal, team=Riverside Athletic, opponent=Northgate Rovers, team_xg=0.23, opponent_xg=1.57, team_shots=1, opponent_shots=13, assist=Kalani Akana, assist_difficulty=6.1, player_goals=1, momentum=20

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-red_card-000553` | 38:05 | pass | Kwabena Darko-Mensah | RIV | 27.4, 26.8 |
| `demo-red_card-000554` | 38:11 | carry | Iñigo Larrazabal | RIV | 9.3, 11.2 |
| `demo-red_card-000555` | 38:15 | pass | Iñigo Larrazabal | RIV | 22.8, 5.9 |
| `demo-red_card-000556` | 38:22 | pass | Kalani Akana | RIV | 58.1, 45.5 |
| `demo-red_card-000557` | 38:28 | carry | Dmytro Lysenko-Vale | RIV | 81.2, 35.2 |
| `demo-red_card-000558` | 38:30 | shot | Dmytro Lysenko-Vale | RIV | 98.1, 40.0 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Dmytro Lysenko-Vale levels it for Riverside Athletic: 1-1 in the 39th minute. | not budgeted | model, verified |
| Fan roaming in Dubai | watch (ar) | Dmytro Lysenko-Vale يعادل النتيجة [1-1] | 0.55 KB | model, verified |
| Commuter, Jakarta | sms (id) | Menit 39: Dmytro Lysenko-Vale samakan skor untuk Riverside Athletic, 1-1. | 0.2 KB, 1 seg GSM-7 | model, verified |
| Student, Delhi | sms (hi) | Dmytro Lysenko-Vale ने Kalani Akana के पास पर गोल कर Riverside Athletic को 1-1 से बराबरी दिलाई। | 0.4 KB, 2 seg UCS-2 | model, verified |

### 43:02 momentum_swing (`demo-red_card-mom-0004`)

Facts: minute=44, match_clock=43:02, score=1-1, team_code=RIV, momentum_now=48, momentum_5min_ago=4, swing=52, team=Riverside Athletic, opponent=Northgate Rovers, team_xg=0.38, opponent_xg=1.57, team_shots=3, opponent_shots=13

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-red_card-000617` | 42:39 | pressure | Jae-won Seo | NOR | 35.6, 51.0 |
| `demo-red_card-000618` | 42:42 | pass | Chidubem Nwachukwu-Bello | RIV | 68.9, 17.0 |
| `demo-red_card-000619` | 42:45 | pass | Matteo Calvisano | RIV | 69.8, 40.6 |
| `demo-red_card-000620` | 42:50 | pass | Dmytro Lysenko-Vale | RIV | 88.1, 30.6 |
| `demo-red_card-000621` | 42:56 | pass | Hiroki Tanabe-Ross | RIV | 69.0, 33.6 |
| `demo-red_card-000622` | 43:02 | carry | Rafael Antunes Beira | RIV | 46.4, 55.2 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Student, Delhi | sms (hi) | 44वें मिनट में Riverside Athletic के पक्ष में लय पलटी, स्कोर 1-1। | 0.2 KB, 1 seg UCS-2 | model, verified |
| Studio analyst, London | broadcast (en) | At 44', Riverside Athletic have seized momentum against Northgate Rovers. Shots: 3-13; score: 1-1. | not budgeted | model, verified |
| Commuter, Jakarta | sms (id) | Pendukung RIV, momentum beralih ke Riverside Athletic saat skor 1-1, meski Northgate Rovers sudah melepas 13 tembakan. | 0.2 KB, 1 seg GSM-7 | model, verified |

### 47:00 half_time (`demo-red_card-mom-0005`)

Facts: minute=48, match_clock=47:00, score=1-1, home_xg=0.47, away_xg=1.57, home_shots=4, away_shots=13, home_possession=60, away_possession=40, home_pass_accuracy=90, away_pass_accuracy=89, top_performer=Nnamdi Okeke-Rhodes, goals=[{'minute': 17, 'player': 'Nnamdi Okeke-Rhodes', 'team': 'Northgate Rovers'}, {'minute': 39, 'player': 'Dmytro Lysenko-Vale', 'team': 'Riverside Athletic'}]

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-red_card-000683` | 46:38 | pass | Rafael Antunes Beira | RIV | 20.9, 53.6 |
| `demo-red_card-000684` | 46:44 | pass | Lukas Brenneisen | RIV | 16.1, 43.9 |
| `demo-red_card-000685` | 46:52 | carry | Rafael Antunes Beira | RIV | 14.5, 59.2 |
| `demo-red_card-000686` | 46:54 | pass | Rafael Antunes Beira | RIV | 31.4, 60.0 |
| `demo-red_card-000687` | 47:00 | pass | Matteo Calvisano | RIV | 38.9, 51.7 |
| `demo-red_card-000688` | 47:00 | half_time |  |  |  |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | At halftime, Riverside Athletic and Northgate Rovers are level 1-1, but Northgate have looked more dangerous, with 1.57 expected goals. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | ब्रेक: 1-1। Riverside 60% कब्ज़ा, Northgate 13 शॉट। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 45:47 goal (`demo-red_card-mom-0006`)

Facts: minute=46, match_clock=45:47, score=1-2, team_code=NOR, player=Ravi Khatri-Sen, xg=0.43, shot_speed_kmh=82.1, outcome=goal, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=2.0, opponent_xg=0.47, team_shots=14, opponent_shots=4, assist=Piet van Rossenberg, assist_difficulty=8.9, player_goals=1, momentum=-16

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-red_card-000696` | 45:30 | pressure | Kalani Akana | RIV | 65.9, 24.6 |
| `demo-red_card-000697` | 45:32 | carry | Piet van Rossenberg | NOR | 32.7, 43.9 |
| `demo-red_card-000698` | 45:34 | pass | Piet van Rossenberg | NOR | 50.1, 43.9 |
| `demo-red_card-000699` | 45:42 | carry | Ravi Khatri-Sen | NOR | 75.4, 55.0 |
| `demo-red_card-000700` | 45:45 | carry | Ravi Khatri-Sen | NOR | 93.0, 42.5 |
| `demo-red_card-000701` | 45:47 | shot | Ravi Khatri-Sen | NOR | 103.2, 37.9 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Ravi Khatri-Sen puts Northgate Rovers 2-1 ahead; they lead Riverside Athletic 14-4 in shots. | not budgeted | model, verified |
| Fan roaming in Dubai | watch (ar) | هدف Ravi Khatri-Sen لـ Northgate Rovers [1-2] | 0.55 KB | model, verified |
| Student, Delhi | sms (hi) | Ravi Khatri-Sen के गोल से Northgate Rovers 2-1 आगे। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 54:00 momentum_swing (`demo-red_card-mom-0007`)

Facts: minute=55, match_clock=54:00, score=1-2, team_code=RIV, momentum_now=44, momentum_5min_ago=12, swing=56, team=Riverside Athletic, opponent=Northgate Rovers, team_xg=0.57, opponent_xg=2.0, team_shots=6, opponent_shots=14

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-red_card-000815` | 53:37 | pass | Thiago Esquível | RIV | 91.9, 54.1 |
| `demo-red_card-000816` | 53:38 | shot | Kalani Akana | RIV | 93.0, 17.8 |
| `demo-red_card-000817` | 53:38 | possession_change | Henrik Solvang | NOR | 1.0, 31.8 |
| `demo-red_card-000818` | 53:45 | pass | Henrik Solvang | NOR | 1.0, 31.8 |
| `demo-red_card-000819` | 53:52 | pass | Kyrylo Bondar | NOR | 4.8, 54.0 |
| `demo-red_card-000820` | 54:00 | pass | Emeka Obiora-Lane | NOR | 19.7, 40.7 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Riverside Athletic’s momentum has surged by 56, but they trail Northgate Rovers 1-2. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Riverside Athletic का दबाव बढ़ा, Northgate Rovers 1-2 से आगे। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 67:36 red_card (`demo-red_card-mom-0009`)

Facts: minute=68, match_clock=67:36, score=1-2, team_code=RIV, player=Matteo Calvisano, team=Riverside Athletic, team_fouls=3, players_left=10

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-red_card-001039` | 67:18 | foul | Mathis Delacour | NOR | 58.7, 15.6 |
| `demo-red_card-001040` | 67:32 | pass | Iñigo Larrazabal | RIV | 46.3, 52.4 |
| `demo-red_card-001041` | 67:36 | tackle | Ravi Khatri-Sen | NOR | 51.5, 40.1 |
| `demo-red_card-001042` | 67:36 | possession_change | Ravi Khatri-Sen | NOR | 51.5, 40.9 |
| `demo-red_card-001043` | 67:36 | tackle | Matteo Calvisano | RIV | 53.5, 27.1 |
| `demo-red_card-001044` | 67:36 | foul | Matteo Calvisano | RIV | 53.5, 27.1 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Matteo Calvisano's red card leaves Riverside Athletic with 10 players, trailing Northgate Rovers 1-2. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Matteo Calvisano को रेड कार्ड; RIV 10 पर, स्कोर 1-2। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 69:45 goal (`demo-red_card-mom-0010`)

Facts: minute=70, match_clock=69:45, score=2-2, team_code=RIV, player=Kalani Akana, xg=0.98, shot_speed_kmh=93.0, outcome=goal, team=Riverside Athletic, opponent=Northgate Rovers, team_xg=1.55, opponent_xg=2.1, team_shots=7, opponent_shots=17, assist=Iñigo Larrazabal, assist_difficulty=8.0, player_goals=1, momentum=28

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-red_card-001068` | 69:28 | pressure | Nnamdi Okeke-Rhodes | NOR | 66.0, 16.5 |
| `demo-red_card-001069` | 69:28 | carry | Iñigo Larrazabal | RIV | 30.1, 55.8 |
| `demo-red_card-001070` | 69:31 | pass | Iñigo Larrazabal | RIV | 42.0, 49.6 |
| `demo-red_card-001071` | 69:39 | carry | Kalani Akana | RIV | 73.2, 19.1 |
| `demo-red_card-001072` | 69:43 | carry | Kalani Akana | RIV | 87.9, 29.1 |
| `demo-red_card-001073` | 69:45 | shot | Kalani Akana | RIV | 104.8, 34.4 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Kalani Akana levels it at 2-2 for Riverside against Northgate, despite Riverside having just 7 shots. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Kalani Akana के गोल से Riverside Athletic ने Northgate Rovers के खिलाफ 2-2 की बराबरी की! | 0.4 KB, 2 seg UCS-2 | model, verified |
| Commuter, Jakarta | sms (id) | Kalani Akana samakan skor 2-2 untuk Riverside Athletic vs Northgate Rovers. | 0.2 KB, 1 seg GSM-7 | model, verified |
| Fan roaming in Dubai | watch (ar) | كالاني أكانا يعيد التعادل [2-2] | 0.55 KB | model, verified |

### 72:20 goal (`demo-red_card-mom-0011`)

Facts: minute=73, match_clock=72:20, score=3-2, team_code=RIV, player=Hiroki Tanabe-Ross, xg=0.76, shot_speed_kmh=105.0, outcome=goal, team=Riverside Athletic, opponent=Northgate Rovers, team_xg=2.55, opponent_xg=2.1, team_shots=9, opponent_shots=17, assist=Thiago Esquível, assist_difficulty=3.2, player_goals=1, momentum=44

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-red_card-001087` | 71:42 | shot | Kalani Akana | RIV | 104.8, 29.8 |
| `demo-red_card-001088` | 72:08 | pass | Dmytro Lysenko-Vale | RIV | 104.5, 67.5 |
| `demo-red_card-001089` | 72:11 | pass | Thiago Esquível | RIV | 94.7, 40.7 |
| `demo-red_card-001090` | 72:16 | pressure | Emeka Obiora-Lane | NOR | 15.0, 31.5 |
| `demo-red_card-001091` | 72:18 | carry | Hiroki Tanabe-Ross | RIV | 84.3, 36.9 |
| `demo-red_card-001092` | 72:20 | shot | Hiroki Tanabe-Ross | RIV | 101.7, 34.3 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Hiroki Tanabe-Ross scores in the 73rd minute to put Riverside Athletic 3-2 ahead of Northgate Rovers. | not budgeted | model, verified |
| Fan roaming in Dubai | watch (ar) | هدف Hiroki Tanabe-Ross لـ Riverside [3-2] | 0.54 KB | model, verified |
| Commuter, Jakarta | sms (id) | Gol Hiroki Tanabe-Ross bawa Riverside Athletic unggul 3-2 atas Northgate Rovers, meski kalah jumlah tembakan. | 0.2 KB, 1 seg GSM-7 | model, verified |
| Student, Delhi | sms (hi) | 73वें मिनट में Hiroki Tanabe-Ross के गोल से Riverside Athletic, Northgate Rovers पर 3-2 से आगे। | 0.4 KB, 2 seg UCS-2 | model, verified |

### 83:00 momentum_swing (`demo-red_card-mom-0012`)

Facts: minute=84, match_clock=83:00, score=3-2, team_code=RIV, momentum_now=36, momentum_5min_ago=20, swing=56, team=Riverside Athletic, opponent=Northgate Rovers, team_xg=2.57, opponent_xg=2.1, team_shots=10, opponent_shots=17

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-red_card-001266` | 82:54 | pass | Seamus Corrigan-Doyle | RIV | 60.6, 45.2 |
| `demo-red_card-001267` | 82:57 | pressure | Mathis Delacour | NOR | 51.0, 33.4 |
| `demo-red_card-001268` | 82:58 | pass | Hiroki Tanabe-Ross | RIV | 54.9, 34.8 |
| `demo-red_card-001269` | 82:58 | interception | Mathis Delacour | NOR | 55.7, 31.4 |
| `demo-red_card-001270` | 82:58 | possession_change | Mathis Delacour | NOR | 52.9, 32.4 |
| `demo-red_card-001271` | 83:00 | pass | Mathis Delacour | NOR | 52.9, 32.4 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Riverside Athletic’s momentum rose from 20 to 36 as they lead Northgate Rovers 3-2. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Riverside Athletic 3-2 से आगे, रफ्तार तेज़। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 85:17 goal (`demo-red_card-mom-0014`)

Facts: minute=86, match_clock=85:17, score=4-2, team_code=RIV, player=Bastien Morvan, xg=0.97, shot_speed_kmh=107.5, outcome=goal, team=Riverside Athletic, opponent=Northgate Rovers, team_xg=3.54, opponent_xg=2.1, team_shots=11, opponent_shots=17, assist=Yusuf Karadağlı, assist_difficulty=7.0, player_goals=1, momentum=60

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-red_card-001310` | 84:53 | pressure | Mathis Delacour | NOR | 65.2, 32.5 |
| `demo-red_card-001311` | 84:55 | pass | Hiroki Tanabe-Ross | RIV | 39.8, 34.7 |
| `demo-red_card-001312` | 85:04 | pass | Yusuf Karadağlı | RIV | 29.0, 11.5 |
| `demo-red_card-001313` | 85:10 | carry | Bastien Morvan | RIV | 71.6, 30.0 |
| `demo-red_card-001314` | 85:15 | carry | Bastien Morvan | RIV | 86.8, 39.7 |
| `demo-red_card-001315` | 85:17 | shot | Bastien Morvan | RIV | 104.8, 31.7 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | At 85:17, Bastien Morvan puts Riverside Athletic 4-2 ahead, despite Northgate Rovers having 17 shots to Riverside's 11. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Bastien Morvan का गोल! Riverside Athletic 4-2 से आगे; Northgate Rovers पर दबाव बढ़ा। | 0.4 KB, 2 seg UCS-2 | model, verified |

### 93:00 full_time (`demo-red_card-mom-0015`)

Facts: minute=94, match_clock=93:00, score=4-2, home_xg=3.54, away_xg=2.1, home_shots=11, away_shots=17, home_possession=59, away_possession=41, home_pass_accuracy=90, away_pass_accuracy=86, top_performer=Ravi Khatri-Sen, goals=[{'minute': 17, 'player': 'Nnamdi Okeke-Rhodes', 'team': 'Northgate Rovers'}, {'minute': 39, 'player': 'Dmytro Lysenko-Vale', 'team': 'Riverside Athletic'}, {'minute': 46, 'player': 'Ravi Khatri-Sen', 'team': 'Northgate Rovers'}, {'minute': 70, 'player': 'Kalani Akana', 'team': 'Riverside Athletic'}, {'minute': 73, 'player': 'Hiroki Tanabe-Ross', 'team': 'Riverside Athletic'}, {'minute': 86, 'player': 'Bastien Morvan', 'team': 'Riverside Athletic'}]

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-red_card-001417` | 92:46 | pass | Seamus Corrigan-Doyle | RIV | 66.6, 49.4 |
| `demo-red_card-001418` | 92:46 | interception | Nnamdi Okeke-Rhodes | NOR | 42.4, 15.9 |
| `demo-red_card-001419` | 92:46 | possession_change | Nnamdi Okeke-Rhodes | NOR | 40.7, 17.0 |
| `demo-red_card-001420` | 92:50 | pass | Nnamdi Okeke-Rhodes | NOR | 40.7, 17.0 |
| `demo-red_card-001421` | 92:57 | pass | Oluwaseun Adebanjo-Cole | NOR | 10.8, 28.7 |
| `demo-red_card-001422` | 93:00 | full_time |  |  |  |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Full-time: Riverside Athletic beat Northgate Rovers 4-2. Ravi Khatri-Sen is player of the match. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Riverside Athletic ने Northgate Rovers को 4-2 से हराया। गोल: Kalani Akana, Hiroki Tanabe-Ross, Bastien Morvan. | 0.4 KB, 2 seg UCS-2 | model, verified |

## Full-time digests

| Fan | Text | Size |
|---|---|---|
| Student, Delhi | Riverside Athletic ने Northgate Rovers को 4-2 से हराया। गोल: Kalani Akana, Hiroki Tanabe-Ross, Bastien Morvan. | 0.4 KB |
