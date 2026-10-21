# MatchGist

**The match, sized to fit every fan.** Not every fan watches on a big screen with fast Wi-Fi. MatchGist
explains what happened in a synthetic football match and why it mattered, then fits it to what each fan has:
an SMS, a short voice note, a watch glance or a full overlay, in their language and within their data budget.

> Work in progress for Microsoft's *Inside the Game* Developer Hackathon. All clubs, players, matches and fans
> are fictional. See `SPEC.md` for the design and `docs/PROGRESS.md` for status.

## Run it (Windows PowerShell)

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# tests and lint
pytest -q
ruff check . ; ruff format --check .

# generate a match (writes ..\matches\m001.jsonl)
python -m app.simulator --seed 42 --storyline comeback --out ..\matches\m001.jsonl

# start the API on http://127.0.0.1:8000  (docs at /docs)
uvicorn app.main:app --reload
```

Try the API from a second PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod -Method Post http://127.0.0.1:8000/matches -ContentType "application/json" -Body '{"seed": 42, "speed": 60, "storyline": "late_drama"}'
Invoke-RestMethod http://127.0.0.1:8000/fans
```

## Repo layout

| Path | What |
|---|---|
| `backend/app/simulator/` | Seeded match simulator, event schema, storylines |
| `backend/app/fans/` | Fan profile model |
| `backend/app/{stats,state,moments,channels,agents,voice}/` | Coming in M2 to M4 (see SPEC section 15) |
| `data/` | Fictional clubs and the six demo fan personas |
| `docs/event-schema.md` | Event schema and fan profile reference |
| `legacy/` | First prototype (Touchline), used as a source of parts and removed before submission |
