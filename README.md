# MatchGist

**The match, sized to fit every fan.** Not every fan watches on a big screen with fast Wi-Fi. MatchGist
explains what happened in a synthetic football match and why it mattered, then fits it to what each fan has:
an SMS, a short voice note, a watch glance or a full overlay, in their language and within their data budget.

> Work in progress for Microsoft's *Inside the Game* Developer Hackathon. All clubs, players, matches and fans
> are fictional. See `SPEC.md` for the design and `docs/PROGRESS.md` for status.

## Run it (Windows PowerShell)

First time only. If `py` isn't recognised (common with a per-user Python install), call Python by its full path:

```powershell
cd backend
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" -m venv .venv   # or: py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1      # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -e ".[dev]"
```

Each new PowerShell window:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
```

Test, lint, generate a match, start the API:

```powershell
pytest -q
ruff check . ; ruff format --check .
python -m app.simulator --seed 42 --storyline comeback --out ..\matches\m001.jsonl
uvicorn app.main:app --reload       # http://127.0.0.1:8000/docs
```

Watch a match live from a second PowerShell window. Four demo matches (seed 42: `none`, `comeback`,
`red_card`, `late_drama`) are prepared at startup and play at 60x:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/matches
curl.exe -N http://127.0.0.1:8000/matches/demo-late_drama/stream
Invoke-RestMethod http://127.0.0.1:8000/matches/demo-late_drama/state
Invoke-RestMethod -Method Post http://127.0.0.1:8000/matches -ContentType "application/json" -Body '{"seed": 7, "speed": 10, "storyline": "comeback"}'
```

## API

| Method | Path | What |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/matches` | Simulate a match `{seed, speed, storyline}`; returns `match_id`, event count, final score |
| GET | `/matches` | All matches with status `ready`, `live` or `finished` |
| GET | `/matches/{id}/stream` | Server-Sent Events: `snapshot`, then `event`, `stats` (every 15 match-seconds and after each moment), `moment`, and finally `end`. One playback per match, shared by every viewer; it starts with the first viewer. |
| GET | `/matches/{id}/state` | Match State snapshot with player stats, moments so far and the momentum series |
| GET | `/fans` | The six demo personas |

## Repo layout

| Path | What |
|---|---|
| `backend/app/simulator/` | Seeded match simulator, event schema, storylines |
| `backend/app/fans/` | Fan profile model |
| `backend/app/channels/` | SMS encoding (GSM-7/UCS-2 segments), channel limits, size model |
| `backend/app/stats/`, `state/`, `moments/` | Stats Engine, Match State, Moment Detector |
| `backend/app/runtime.py` | Shared live playback per match |
| `backend/app/{agents,voice}/` | Coming in M3 and M4 (see SPEC section 15) |
| `data/` | Fictional clubs and the six demo fan personas |
| `docs/event-schema.md` | Event schema and fan profile reference |
| `legacy/` | First prototype (Touchline), used as a source of parts and removed before submission |
