"""Record full matches through the real pipeline, for the static replay site and the evidence folder.

Each storyline is played event by event through the Stats Engine, Moment Detector and agent workflow (with
whatever model ``.env`` configures, or the offline templates). Every message the live SSE stream would send
is stamped with its match time, so the browser can replay it at any speed with no server at all.

    python -m app.record                     # all storylines -> frontend/public/replays + evidence/
    python -m app.record --storyline comeback
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from collections import Counter
from typing import Any, get_args

from app.agents.llm import LLMSettings
from app.config import REPO_ROOT
from app.fans.profiles import load_fans
from app.runtime import MatchRuntime
from app.simulator.engine import _delays, generate_match
from app.simulator.schema import Storyline

STATS_EVERY_S = 30.0  # fewer snapshots than live: the file is downloaded whole
REPLAYS = REPO_ROOT / "frontend" / "public" / "replays"
EVIDENCE = REPO_ROOT / "evidence"
EVIDENCE_FANS = ("fan_london", "fan_delhi", "fan_jakarta", "fan_dubai")


async def record(storyline: str, seed: int = 42, settings: LLMSettings | None = None) -> dict[str, Any]:
    """Play one match through the whole pipeline and return the replay document."""
    match = generate_match(seed, storyline, f"demo-{storyline}")
    rt = MatchRuntime(match, speed=1.0, fans=load_fans(), settings=settings or LLMSettings.from_env())
    out: list[list[Any]] = []
    now = [0.0]
    rt._publish = lambda name, payload: out.append([round(now[0], 1), name, payload])  # type: ignore[method-assign]

    first = rt.snapshot_payload()
    first["names"] = rt.state.names
    out.append([0.0, "snapshot", first])
    next_stats, last_minute = 0.0, 0
    # playback seconds at 1x, with the half-time break skipped, exactly as the live stream paces it
    for wait, ev in _delays(match, 1.0):
        now[0] += wait
        moments = rt.analyzer.feed(ev)
        rt._publish("event", ev.model_dump(exclude_none=True))
        for m in moments:
            rt._publish("moment", m.model_dump())
        for m in moments:
            await rt.orchestrator.on_moment(m)
        if rt.state.minute != last_minute and ev.type != "full_time":
            last_minute = rt.state.minute
            await rt.orchestrator.tick(float(last_minute))
        if moments or now[0] >= next_stats or ev.type in ("half_time", "full_time"):
            next_stats = now[0] + STATS_EVERY_S
            rt._publish("stats", rt.snapshot_payload())
    rt._publish("stats", rt.snapshot_payload())
    rt._publish("end", rt.end_payload())
    return {
        "meta": {
            "storyline": storyline,
            "seed": seed,
            "model": rt.orchestrator.model_label,
            "recorded_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
            "final_score": list(match.final_score),
            "home": match.home.name,
            "away": match.away.name,
            "duration_s": round(now[0], 1),
        },
        "messages": out,
    }


# ---------------------------------------------------------------------- evidence
def _md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def evidence_markdown(doc: dict[str, Any]) -> str:
    """A readable trail for one match: moments, their source events, three fans' outputs, Verifier tally."""
    meta, msgs = doc["meta"], doc["messages"]
    names: dict[str, str] = msgs[0][2].get("names", {})
    events = {p["event_id"]: p for _, n, p in msgs if n == "event"}
    moments = [p for _, n, p in msgs if n == "moment"]
    deliveries = [p for _, n, p in msgs if n == "delivery"]
    agent = [p for _, n, p in msgs if n == "agent_event"]
    fans = {f["fan_id"]: f for f in msgs[0][2]["fans"]}

    score = "-".join(str(g) for g in meta["final_score"])
    lines = [
        f"# {meta['storyline']}: {meta['home']} {score} {meta['away']}",
        "",
        f"Seed {meta['seed']}, model `{meta['model']}`, recorded {meta['recorded_at']}.",
        "Synthetic match, fictional clubs and players.",
        "",
        f"{len(events)} events, {len(moments)} moments, {len(deliveries)} deliveries to {len(fans)} fans.",
        "",
        "## Grounding check (the Verifier)",
        "",
    ]
    writer = "offline templates" if meta["model"].startswith("offline") else "model"
    ver = Counter(e["action"] for e in agent if e["agent"] == "verifier")
    fb = Counter(e["agent"] for e in agent if e["action"] == "fallback")
    by_model = sum(1 for d in deliveries if not d["fallback_used"])
    lines += [
        "| Result | Count |",
        "|---|---|",
        f"| Verifier passed | {ver.get('pass', 0)} |",
        f"| Verifier rejected, sent back to the Compressor | {ver.get('reject', 0)} |",
        f"| Fell back to a template after rejections | {ver.get('fallback', 0)} |",
        f"| Deliveries written by the {writer} (and verified) | {by_model} |",
        f"| Deliveries from a fallback template | {len(deliveries) - by_model} |",
        "",
        "Template fallbacks by agent: "
        + (", ".join(f"{k} {v}" for k, v in sorted(fb.items())) or "none")
        + ".",
        "",
        "## Moments and their source events",
        "",
    ]
    for m in moments:
        if m["base_score"] < 50:
            continue
        facts = ", ".join(
            f"{k}={v}" for k, v in m["facts"].items() if k not in ("home", "away", "home_code", "away_code")
        )
        lines += [
            f"### {m['match_clock']} {m['type']} (`{m['moment_id']}`)",
            "",
            f"Facts: {_md_escape(facts)}",
            "",
        ]
        lines += ["| Event | Time | Type | Player | Team | x, y |", "|---|---|---|---|---|---|"]
        for eid in m.get("source_event_ids", []):
            e = events.get(eid)
            if not e:
                continue
            who = names.get(e.get("player_id", ""), e.get("player_id", ""))
            xy = f"{e['x']}, {e['y']}" if "x" in e and "y" in e else ""
            lines.append(
                f"| `{eid}` | {e.get('match_clock', '')} | {e['type']} | {who} | "
                f"{e.get('team_id', '')} | {xy} |"
            )
        lines += [
            "",
            "What each fan received:",
            "",
            "| Fan | Channel | Text | Size | Source |",
            "|---|---|---|---|---|",
        ]
        for d in deliveries:
            if m["moment_id"] in d["moment_ids"] and d["fan_id"] in EVIDENCE_FANS:
                f = fans[d["fan_id"]]
                text = d["text"] if not d.get("value") else f"{d['text']} [{d['value']}]"
                if d.get("title"):
                    text = f"{d['title']}: {text}"
                size = (
                    "not budgeted"
                    if d["kind"] == "overlay"
                    else f"{d['size_kb']} KB"
                    + (f", {d['segments']} seg {d['encoding']}" if d.get("segments") else "")
                )
                lines.append(
                    f"| {f['display_name']} | {d['channel']} ({d['language']}) | {_md_escape(text)} | "
                    f"{size} | {'fallback template' if d['fallback_used'] else writer + ', verified'} |"
                )
        lines.append("")
    lines += ["## Full-time digests", "", "| Fan | Text | Size |", "|---|---|---|"]
    for d in deliveries:
        if d["kind"] == "digest":
            lines.append(
                f"| {fans[d['fan_id']]['display_name']} | {_md_escape(d['text'])} | {d['size_kb']} KB |"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--storyline", choices=list(get_args(Storyline)), action="append")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    settings = LLMSettings.from_env()
    REPLAYS.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    index = []
    for storyline in args.storyline or list(get_args(Storyline)):
        started = time.perf_counter()
        doc = asyncio.run(record(storyline, args.seed, settings))
        path = REPLAYS / f"{storyline}.json"
        path.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        (EVIDENCE / f"{storyline}.md").write_text(evidence_markdown(doc), encoding="utf-8")
        index.append(doc["meta"])
        print(
            f"{storyline}: {len(doc['messages'])} messages, {path.stat().st_size // 1024} KB, "
            f"model {doc['meta']['model']}, {time.perf_counter() - started:.0f}s"
        )
    existing = REPLAYS / "index.json"
    known = {m["storyline"]: m for m in (json.loads(existing.read_text()) if existing.exists() else [])}
    known.update({m["storyline"]: m for m in index})
    existing.write_text(json.dumps(list(known.values()), ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
