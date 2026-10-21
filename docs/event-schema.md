# Event schema v1 and fan profile

Source of truth: `backend/app/simulator/schema.py` (events) and `backend/app/fans/profiles.py` (fans).
Every event in `matches/*.jsonl` validates against these models (tested).

## Conventions

| Topic | Rule |
|---|---|
| Pitch | 105 × 68 m |
| Coordinates | **Team-relative.** `x` runs 0–105 from the acting team's own goal (`team_id`) to the goal it attacks. `y` runs 0–68 across the pitch. Renderers mirror away-team events and the second half. |
| Clock | `match_clock` is `MM:SS`. The first half runs from `00:00` (stoppage time continues past `45:00`); the second half restarts at `45:00`. Order events by `(period, match_clock)`. |
| Order | `seq` starts at 1 and increases by 1 for every event in the match. `event_id` = `<match_id>-<seq, 6 digits>`. |
| Ids | Players are `CLB-NN` (club code and shirt number), clubs are three capital letters. |
| `meta` | Extra simulator detail. Consumers must not rely on it. |

## Common fields

| Field | Type | Notes |
|---|---|---|
| `event_id` | str | unique |
| `match_id` | str | |
| `seq` | int ≥ 1 | strictly increasing |
| `match_clock` | `MM:SS` | see above |
| `period` | 1 or 2 | |
| `type` | str | one of the types below |
| `team_id` | str or null | acting team |
| `player_id` | str or null | acting player |
| `x`, `y` | float or null | where the action started (team-relative) |
| `meta` | object | |

## Types

| type | Extra fields | Meaning |
|---|---|---|
| `kickoff` | — | Start of each half and restart after a goal. `meta.after_goal` / `meta.second_half`. |
| `half_time`, `full_time` | — | `meta.score` = `[home, away]` |
| `pass` | `end_x`, `end_y`, `outcome` (`complete`/`incomplete`), `receiver_id` (intended), `pressure` 0–1, `speed_kmh` (ball) | `meta.x_completion` = the simulator's completion probability; `meta.cross` |
| `carry` | `end_x`, `end_y`, `distance_m`, `speed_kmh` | Runs with the ball of 5 m or more |
| `shot` | `outcome` (`goal`/`saved`/`off_target`/`blocked`), `speed_kmh`, `xg`, `pressure` | A goal is a shot with `outcome: goal`. `meta.header`, `meta.distance_m` |
| `tackle` | `outcome` (`won`/`lost`), `opponent_id` | A lost tackle may be followed by a `foul` |
| `interception` | — | Player who cut out a pass |
| `foul` | `card` (`none`/`yellow`/`red`) | A second yellow is reported as `red`. `meta.fouled` = the fouled player |
| `possession_change` | `from_team`, `to_team`, `cause` | `cause` ∈ interception, tackle, save, block, goal_kick, kick_off, foul, throw_in, half_time |
| `pressure` | `target_player_id`, `intensity` 0–1 | A pressing action: an opponent who was 8 m+ away when the player received the ball closes them down to within 1.2 m |
| `substitution` | `player_off`, `player_on` | `player_id` = `player_on` |

### Example

```json
{"event_id":"m001-000412","match_id":"m001","seq":412,"match_clock":"34:12","period":1,"type":"pass",
 "team_id":"RIV","player_id":"RIV-08","x":46.2,"y":31.0,"end_x":71.5,"end_y":18.4,"outcome":"complete",
 "receiver_id":"RIV-10","pressure":0.62,"speed_kmh":58.3,"meta":{"x_completion":0.71,"cross":false}}
```

## How the simulator produces realistic numbers

The simulator is a possession-chain model running on light physics: 22 players with speed and acceleration
limits, moving toward tactical targets.

- **Pass success** uses an expected-completion model: distance, how open the passing lane is, pressure on
  the passer, and the passing rating. About a third of misplaced passes go out for a throw-in.
- **Shots** use a distance/angle xG model with header and pressure penalties. Shot speed scales with the
  shooting rating.
- **Tackles** set the defending rating against the carrier's pace.
- **Pressing** depends on club style and on how close the ball is to the defending team's goal.

Calibration across 60 seeds: 1,331–1,482 events per match, 2.4 goals, ~21 shots, 88% pass completion and
2.8 yellow cards per match on average. Midfielders make ~40% of passes and defenders ~30%. Goals are spread across
the front three. Pass choice depends on the passer's third of the pitch (build through the back, find forwards in
the final third), wingers cut inside or cross, and midfielders shoot from distance. Northgate (direct, quicker)
is the slightly stronger side.

### Storylines

`none`, `comeback` (the team trailing at 70' finishes level or ahead), `red_card` and `late_drama` (a goal
after 85' that changes the result). Each storyline biases finishing and shooting by minute, or schedules a
red card. Derived sub-seeds (`seed*1000+i`) are then tried in order until the finished match satisfies the
storyline, so the same `(seed, storyline)` always gives the same match. `Match.sim_seed` records which
sub-seed was used.

## Fan profile

| Field | Type | Values |
|---|---|---|
| `fan_id` | str | lowercase, digits, `_` |
| `display_name` | str | |
| `language` | str | `en`, `hi`, `id`, `pt-BR`, `ar`, `pcm` |
| `mode` | str | `analyst`, `casual`, `club_focus`, `player_focus`, `single_metric` |
| `favorite_club` | str or null | e.g. `RIV` (required for `club_focus` and `only_if_involved`) |
| `favorite_player` | str or null | e.g. `RIV-10` (required for `player_focus`) |
| `focus_metric` | str or null | `xg`, `possession`, `momentum`, `pressure`, `pass_accuracy`, `shot_speed` (required for `single_metric`) |
| `channel` | str | `broadcast`, `sms`, `chat`, `voice`, `watch`, `push` |
| `data_budget_kb` | number or null | null = unlimited |
| `max_pings` | int or null | null = unlimited |
| `only_if_involved` | bool | only moments involving the favourite club or player |
| `quiet_after_minute` | int or null | |

The six demo personas are in `data/fans.json`.
