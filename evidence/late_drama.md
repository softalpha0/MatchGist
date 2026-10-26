# late_drama: Riverside Athletic 1-2 Northgate Rovers

Seed 42, model `openai-compatible:gpt-6-luna`, recorded 2026-10-26 04:14 UTC.
Synthetic match, fictional clubs and players.

1371 events, 17 moments, 46 deliveries to 6 fans.

## Grounding check (the Verifier)

| Result | Count |
|---|---|
| Verifier passed | 46 |
| Verifier rejected, sent back to the Compressor | 4 |
| Fell back to a template after rejections | 0 |
| Deliveries written by the model (and verified) | 46 |
| Deliveries from a fallback template | 0 |

Template fallbacks by agent: none.

## Moments and their source events

### 16:14 big_chance (`demo-late_drama-mom-0001`)

Facts: minute=17, match_clock=16:14, score=0-0, team_code=NOR, player=Nnamdi Okeke-Rhodes, xg=0.49, shot_speed_kmh=104.4, outcome=saved, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=0.78, opponent_xg=0.0, team_shots=5, opponent_shots=0

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-late_drama-000232` | 15:43 | pressure | Nnamdi Okeke-Rhodes | NOR | 97.5, 57.2 |
| `demo-late_drama-000233` | 15:45 | pass | Iñigo Larrazabal | RIV | 6.5, 10.3 |
| `demo-late_drama-000234` | 16:05 | possession_change | Nnamdi Okeke-Rhodes | NOR | 81.4, 67.7 |
| `demo-late_drama-000235` | 16:09 | carry | Nnamdi Okeke-Rhodes | NOR | 81.4, 67.7 |
| `demo-late_drama-000236` | 16:13 | carry | Nnamdi Okeke-Rhodes | NOR | 88.4, 47.5 |
| `demo-late_drama-000237` | 16:14 | shot | Nnamdi Okeke-Rhodes | NOR | 100.6, 33.5 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Nnamdi Okeke-Rhodes’s 0.49 xG chance is saved; Riverside Athletic and Northgate Rovers remain level at 0-0. | not budgeted | model, verified |
| Fan roaming in Dubai | watch (ar) | تصدى الحارس لمحاولة Nnamdi Okeke-Rhodes [0-0] | 0.56 KB | model, verified |
| Student, Delhi | sms (hi) | Nnamdi Okeke-Rhodes का शॉट बचा; स्कोर 0-0। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 32:03 momentum_swing (`demo-late_drama-mom-0005`)

Facts: minute=33, match_clock=32:03, score=0-0, team_code=NOR, momentum_now=56, momentum_5min_ago=12, swing=68, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=1.1, opponent_xg=0.02, team_shots=9, opponent_shots=1

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-late_drama-000454` | 31:33 | pass | Mikael Brandvold | RIV | 5.5, 34.0 |
| `demo-late_drama-000455` | 31:38 | pass | Kwabena Darko-Mensah | RIV | 2.6, 26.4 |
| `demo-late_drama-000456` | 31:45 | pass | Iñigo Larrazabal | RIV | 6.6, 11.9 |
| `demo-late_drama-000457` | 31:50 | pass | Rafael Antunes Beira | RIV | 8.2, 52.6 |
| `demo-late_drama-000458` | 31:56 | pass | Lukas Brenneisen | RIV | 4.4, 43.9 |
| `demo-late_drama-000459` | 32:03 | pass | Matteo Calvisano | RIV | 22.7, 48.9 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Northgate Rovers have seized momentum with a rating of 56, but remain level 0-0 with Riverside Athletic. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Northgate Rovers का पलड़ा भारी; स्कोर 0-0, स्विंग 68। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 47:00 half_time (`demo-late_drama-mom-0006`)

Facts: minute=48, match_clock=47:00, score=0-0, home_xg=0.17, away_xg=1.1, home_shots=4, away_shots=9, home_possession=63, away_possession=37, home_pass_accuracy=94, away_pass_accuracy=89, top_performer=Lorenzo Fabbrini-Neri, goals=[]

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-late_drama-000671` | 46:36 | pass | Iñigo Larrazabal | RIV | 17.7, 10.8 |
| `demo-late_drama-000672` | 46:41 | pass | Thiago Esquível | RIV | 59.9, 9.3 |
| `demo-late_drama-000673` | 46:48 | pass | Hiroki Tanabe-Ross | RIV | 39.2, 30.1 |
| `demo-late_drama-000674` | 46:53 | pass | Kwabena Darko-Mensah | RIV | 21.4, 25.7 |
| `demo-late_drama-000675` | 46:59 | carry | Iñigo Larrazabal | RIV | 21.6, 9.0 |
| `demo-late_drama-000676` | 47:00 | half_time |  |  |  |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | At the break, Riverside Athletic and Northgate Rovers are level at 0-0, with Northgate leading the shot count. | not budgeted | model, verified |
| Commuter, Jakarta | sms (id) | Riverside Athletic unggul penguasaan bola dan akurasi operan; Northgate Rovers lebih mengancam dengan 9 tembakan. Skor jeda 0-0. | 0.2 KB, 1 seg GSM-7 | model, verified |
| Student, Delhi | sms (hi) | हाफ़टाइम: Riverside Athletic 0-0 Northgate Rovers; Northgate के 9 शॉट। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 46:41 goal (`demo-late_drama-mom-0007`)

Facts: minute=47, match_clock=46:41, score=0-1, team_code=NOR, player=Ravi Khatri-Sen, xg=0.92, shot_speed_kmh=105.0, outcome=goal, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=2.02, opponent_xg=0.17, team_shots=10, opponent_shots=4, assist=Emeka Obiora-Lane, assist_difficulty=7.0, player_goals=1, momentum=12

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-late_drama-000697` | 46:17 | pass | Matteo Calvisano | RIV | 51.1, 24.7 |
| `demo-late_drama-000698` | 46:32 | possession_change | Ravi Khatri-Sen | NOR | 76.4, 67.7 |
| `demo-late_drama-000699` | 46:35 | pressure | Lukas Brenneisen | RIV | 19.1, 9.7 |
| `demo-late_drama-000700` | 46:36 | carry | Ravi Khatri-Sen | NOR | 76.4, 67.7 |
| `demo-late_drama-000701` | 46:39 | carry | Ravi Khatri-Sen | NOR | 91.3, 52.4 |
| `demo-late_drama-000702` | 46:41 | shot | Ravi Khatri-Sen | NOR | 104.8, 37.4 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Ravi Khatri-Sen puts Northgate Rovers 1-0 ahead in the 47th minute. | not budgeted | model, verified |
| Fan roaming in Dubai | watch (ar) | هدف Ravi Khatri-Sen يمنح التقدم [0-1] | 0.55 KB | model, verified |
| Student, Delhi | sms (hi) | Ravi Khatri-Sen के 47वें मिनट के गोल से NOR ने 0-1 की बढ़त ली। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 51:03 momentum_swing (`demo-late_drama-mom-0009`)

Facts: minute=52, match_clock=51:03, score=0-1, team_code=NOR, momentum_now=36, momentum_5min_ago=8, swing=44, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=2.05, opponent_xg=0.17, team_shots=11, opponent_shots=4

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-late_drama-000760` | 50:51 | pass | Hiroki Tanabe-Ross | RIV | 28.6, 32.8 |
| `demo-late_drama-000761` | 50:51 | interception | Joaquín Barrenechea | NOR | 80.0, 40.2 |
| `demo-late_drama-000762` | 50:51 | possession_change | Joaquín Barrenechea | NOR | 77.5, 37.2 |
| `demo-late_drama-000763` | 50:54 | pass | Joaquín Barrenechea | NOR | 77.5, 37.2 |
| `demo-late_drama-000764` | 50:58 | pass | Nnamdi Okeke-Rhodes | NOR | 79.3, 17.0 |
| `demo-late_drama-000765` | 51:03 | pass | Lorenzo Fabbrini-Neri | NOR | 68.3, 43.4 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Northgate Rovers have swung momentum by 44 and lead Riverside Athletic 0-1. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Northgate Rovers आगे 0-1; Riverside Athletic पर दबाव, मोमेंटम +44। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 67:05 momentum_swing (`demo-late_drama-mom-0011`)

Facts: minute=68, match_clock=67:05, score=0-1, team_code=RIV, momentum_now=31, momentum_5min_ago=36, swing=67, team=Riverside Athletic, opponent=Northgate Rovers, team_xg=0.25, opponent_xg=2.11, team_shots=6, opponent_shots=14

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-late_drama-001006` | 66:27 | shot | Dmytro Lysenko-Vale | RIV | 88.3, 39.9 |
| `demo-late_drama-001007` | 66:51 | pass | Dmytro Lysenko-Vale | RIV | 104.5, 67.5 |
| `demo-late_drama-001008` | 66:53 | shot | Thiago Esquível | RIV | 96.6, 42.5 |
| `demo-late_drama-001009` | 66:53 | possession_change | Henrik Solvang | NOR | 1.0, 33.5 |
| `demo-late_drama-001010` | 66:59 | pass | Henrik Solvang | NOR | 1.0, 33.5 |
| `demo-late_drama-001011` | 67:05 | carry | Ismael Ferrandis | NOR | 1.8, 8.8 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | At 68 minutes, Riverside Athletic trail Northgate Rovers 0-1, with momentum down to 31. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Riverside Athletic 0-1 से Northgate Rovers से पीछे; रफ्तार घटी। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 78:03 momentum_swing (`demo-late_drama-mom-0014`)

Facts: minute=79, match_clock=78:03, score=0-1, team_code=RIV, momentum_now=28, momentum_5min_ago=36, swing=64, team=Riverside Athletic, opponent=Northgate Rovers, team_xg=0.34, opponent_xg=2.23, team_shots=7, opponent_shots=16

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-late_drama-001177` | 77:30 | carry | Ismael Ferrandis | NOR | 5.0, 21.1 |
| `demo-late_drama-001178` | 77:33 | pass | Ismael Ferrandis | NOR | 22.5, 20.4 |
| `demo-late_drama-001179` | 77:35 | pressure | Kalani Akana | RIV | 74.0, 24.1 |
| `demo-late_drama-001180` | 77:38 | pass | Callum Fairbairn | NOR | 31.6, 43.9 |
| `demo-late_drama-001181` | 77:59 | possession_change | Kalani Akana | RIV | 74.3, 0.3 |
| `demo-late_drama-001182` | 78:03 | carry | Kalani Akana | RIV | 74.3, 0.3 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | At 79 minutes, Riverside Athletic trail Northgate Rovers 0-1, with momentum at 28. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | Riverside Athletic 0-1 से पीछे; Northgate Rovers हावी। | 0.2 KB, 1 seg UCS-2 | model, verified |

### 89:00 goal (`demo-late_drama-mom-0015`)

Facts: minute=90, match_clock=89:00, score=1-1, team_code=RIV, player=Thiago Esquível, xg=0.07, shot_speed_kmh=100.8, outcome=goal, team=Riverside Athletic, opponent=Northgate Rovers, team_xg=0.41, opponent_xg=2.56, team_shots=8, opponent_shots=19, assist=Iñigo Larrazabal, assist_difficulty=4.4, player_goals=1, momentum=16

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-late_drama-001333` | 88:29 | pass | Lukas Brenneisen | RIV | 37.0, 29.6 |
| `demo-late_drama-001334` | 88:36 | pass | Anouar Belkhadem | RIV | 44.5, 22.6 |
| `demo-late_drama-001335` | 88:43 | pass | Iñigo Larrazabal | RIV | 30.6, 54.1 |
| `demo-late_drama-001336` | 88:51 | carry | Thiago Esquível | RIV | 69.5, 56.7 |
| `demo-late_drama-001337` | 88:56 | carry | Thiago Esquível | RIV | 86.4, 62.9 |
| `demo-late_drama-001338` | 89:00 | shot | Thiago Esquível | RIV | 104.3, 46.3 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Thiago Esquível's 89th-minute equalizer makes it 1-1, with Riverside's 0.41 xG trailing Northgate's 2.56. | not budgeted | model, verified |
| Fan roaming in Dubai | watch (ar) | Thiago Esquível يعيد Riverside للتعادل [1-1] | 0.55 KB | model, verified |
| Commuter, Jakarta | sms (id) | Gol Thiago Esquivel menit 89 samakan skor 1-1 untuk RIV kontra Northgate Rovers. | 0.2 KB, 1 seg GSM-7 | model, verified |
| Student, Delhi | sms (hi) | 90वें मिनट में Thiago Esquível के गोल से Riverside Athletic ने Northgate Rovers के साथ 1-1 की बराबरी की! | 0.4 KB, 2 seg UCS-2 | model, verified |

### 91:27 goal (`demo-late_drama-mom-0016`)

Facts: minute=92, match_clock=91:27, score=1-2, team_code=NOR, player=Joaquín Barrenechea, xg=0.17, shot_speed_kmh=91.5, outcome=goal, team=Northgate Rovers, opponent=Riverside Athletic, team_xg=2.73, opponent_xg=0.41, team_shots=20, opponent_shots=8, assist=Emeka Obiora-Lane, assist_difficulty=6.4, player_goals=1, momentum=0

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-late_drama-001354` | 91:01 | pass | Kyrylo Bondar | NOR | 44.7, 65.5 |
| `demo-late_drama-001355` | 91:06 | pass | Ravi Khatri-Sen | NOR | 63.3, 62.5 |
| `demo-late_drama-001356` | 91:10 | pass | Callum Fairbairn | NOR | 53.7, 53.0 |
| `demo-late_drama-001357` | 91:18 | carry | Emeka Obiora-Lane | NOR | 53.4, 38.7 |
| `demo-late_drama-001358` | 91:22 | pass | Emeka Obiora-Lane | NOR | 65.7, 45.0 |
| `demo-late_drama-001359` | 91:27 | shot | Joaquín Barrenechea | NOR | 93.1, 32.5 |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Joaquín Barrenechea scores in the 92nd minute to put Northgate Rovers 2-1 ahead of Riverside Athletic. | not budgeted | model, verified |
| Student, Delhi | sms (hi) | 92वें मिनट में Joaquín Barrenechea के गोल से Northgate Rovers ने Riverside Athletic को 2-1 से हराया। | 0.4 KB, 2 seg UCS-2 | model, verified |
| Fan roaming in Dubai | watch (ar) | هدف متأخر لـ Joaquín Barrenechea [1-2] | 0.54 KB | model, verified |

### 93:17 full_time (`demo-late_drama-mom-0017`)

Facts: minute=94, match_clock=93:17, score=1-2, home_xg=0.41, away_xg=2.73, home_shots=8, away_shots=20, home_possession=57, away_possession=43, home_pass_accuracy=92, away_pass_accuracy=89, top_performer=Ravi Khatri-Sen, goals=[{'minute': 47, 'player': 'Ravi Khatri-Sen', 'team': 'Northgate Rovers'}, {'minute': 90, 'player': 'Thiago Esquível', 'team': 'Riverside Athletic'}, {'minute': 92, 'player': 'Joaquín Barrenechea', 'team': 'Northgate Rovers'}]

| Event | Time | Type | Player | Team | x, y |
|---|---|---|---|---|---|
| `demo-late_drama-001366` | 92:45 | pass | Hiroki Tanabe-Ross | RIV | 39.0, 36.7 |
| `demo-late_drama-001367` | 92:51 | pass | Yusuf Karadağlı | RIV | 27.1, 12.6 |
| `demo-late_drama-001368` | 92:56 | carry | Kwabena Darko-Mensah | RIV | 19.5, 39.0 |
| `demo-late_drama-001369` | 93:00 | pass | Kwabena Darko-Mensah | RIV | 29.3, 41.6 |
| `demo-late_drama-001370` | 93:16 | possession_change | Ismael Ferrandis | NOR | 38.8, 0.3 |
| `demo-late_drama-001371` | 93:17 | full_time |  |  |  |

What each fan received:

| Fan | Channel | Text | Size | Source |
|---|---|---|---|---|
| Studio analyst, London | broadcast (en) | Northgate Rovers beat Riverside Athletic 2-1, with Joaquín Barrenechea’s 92nd-minute goal sealing a dramatic win. | not budgeted | model, verified |
| Fan roaming in Dubai | watch (ar) | فوز Northgate على Riverside [1-2] | 0.54 KB | model, verified |
| Commuter, Jakarta | sms (id) | Riverside Athletic kalah 1-2 dari Northgate Rovers. Ravi Khatri-Sen mencetak gol menit 47, Thiago Esquivel menyamakan menit 90, lalu Joaquin Barrenechea membalas menit 92. | 0.4 KB, 2 seg GSM-7 | model, verified |
| Student, Delhi | sms (hi) | Northgate Rovers ने Riverside Athletic को 2-1 से हराया। 92वें मिनट में Joaquín Barrenechea ने जीत दिलाई। | 0.4 KB, 2 seg UCS-2 | model, verified |

## Full-time digests

| Fan | Text | Size |
|---|---|---|
| Fan roaming in Dubai | فوز Northgate على Riverside | 0.54 KB |
| Office worker, São Paulo | Ravi Khatri-Sen abriu o placar; Joaquín Barrenechea decidiu. xG: 2,73 a 0,41. | 1.11 KB |
| Fan, Lagos | Northgate Rovers beat Riverside Athletic 1-2. Ravi Khatri-Sen score first, Thiago Esquível equalize, but Joaquín Barrenechea get the late winner. | 16.2 KB |
| Commuter, Jakarta | Riverside Athletic kalah 1-2 dari Northgate Rovers. Ravi Khatri-Sen mencetak gol menit 47, Thiago Esquivel menyamakan menit 90, lalu Joaquin Barrenechea membalas menit 92. | 0.4 KB |
| Student, Delhi | Northgate Rovers ने Riverside Athletic को 2-1 से हराया। 92वें मिनट में Joaquín Barrenechea ने जीत दिलाई। | 0.4 KB |
