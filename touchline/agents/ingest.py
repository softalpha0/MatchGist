"""Ingest agent: turns a raw, possibly dirty event feed into clean ``MatchEvent``s.

Real feeds deliver duplicates, late events, impossible coordinates and
references to unknown players. Each problem is repaired or quarantined, and
every decision is reported so operators can see what the agent did.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from touchline.models import PITCH_LENGTH, PITCH_WIDTH, MatchEvent


@dataclass
class IngestReport:
    accepted: int = 0
    duplicates: int = 0
    resequenced: int = 0
    repaired: int = 0
    quarantined: int = 0
    notes: list[str] = field(default_factory=list)


class IngestGate:
    def __init__(self, known_players: set[str]):
        self.known = known_players
        self.seen: set[str] = set()
        self.last_seq = 0

    def process(self, raw: list[dict[str, Any]]) -> tuple[list[MatchEvent], IngestReport]:
        rep = IngestReport()
        clean: list[MatchEvent] = []
        for item in raw:
            try:
                ev = MatchEvent.model_validate(item)
            except ValidationError as exc:
                rep.quarantined += 1
                rep.notes.append(f"quarantined malformed event ({exc.error_count()} schema errors)")
                continue
            if ev.id in self.seen:
                rep.duplicates += 1
                rep.notes.append(f"dropped duplicate {ev.id}")
                continue
            for pid in (ev.player_id, ev.target_id):
                if pid is not None and pid not in self.known:
                    break
            else:
                pid = None
            if pid is not None:
                rep.quarantined += 1
                rep.notes.append(f"quarantined {ev.type.value} with unknown player '{pid}'")
                continue
            fixed = False
            for attr, hi in (
                ("x", PITCH_LENGTH),
                ("end_x", PITCH_LENGTH),
                ("y", PITCH_WIDTH),
                ("end_y", PITCH_WIDTH),
            ):
                v = getattr(ev, attr)
                if v is not None and not 0 <= v <= hi:
                    setattr(ev, attr, min(max(v, 0.0), hi))
                    fixed = True
            if fixed:
                rep.repaired += 1
                rep.notes.append(f"clamped off-pitch coordinates on {ev.id}")
            self.seen.add(ev.id)
            clean.append(ev)
        ordered = sorted(clean, key=lambda e: e.seq)
        if [e.seq for e in ordered] != [e.seq for e in clean]:
            rep.resequenced += sum(1 for a, b in zip(ordered, clean, strict=True) if a.seq != b.seq)
            rep.notes.append(f"re-sequenced {rep.resequenced} out-of-order events")
        late = [e for e in ordered if e.seq < self.last_seq]
        if late:
            rep.notes.append(f"accepted {len(late)} late events")
        if ordered:
            self.last_seq = max(self.last_seq, ordered[-1].seq)
        rep.accepted = len(ordered)
        return ordered, rep
