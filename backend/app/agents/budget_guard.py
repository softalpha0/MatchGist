"""Budget Guard: send now, hold for a bundle, or skip, with a recorded reason (SPEC section 9.2).

Rules, in order:
  1. Broadcast overlays aren't budgeted: anything scoring 30+ goes on screen.
  2. ``only_if_involved`` fans never hear about moments without their club or player.
  3. Nothing after ``quiet_after_minute`` except goals and full time.
  4. No pings or no data left: skip.
  5. Goals always send (while anything remains), and immediately carry any held moments with them.
  6. Otherwise the moment must beat a threshold that rises as pings run out:
     ``50 + 40 * (1 - pings_left / max_pings)`` (50 when pings are unlimited).
  7. Plan ahead: lesser moments never use the last two pings (one kept for a goal, one for the full-time
     digest; just the digest's when the fan has three pings or fewer). From the 75th minute the digest's
     data is reserved too.
  8. A moment that passes is held for up to 2 match-minutes so that close moments travel as one message
     (one ping); a very strong one (85+) goes immediately.
The full-time digest is not decided here: it always gets the reserve.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.agents.ranker import Ranking
from app.fans.profiles import FanProfile
from app.moments.models import Moment
from app.state.ledger import DIGEST_RESERVE_KB, TYPICAL_KB, Ledger

OVERLAY_THRESHOLD = 30
SEND_NOW_SCORE = 85
SEND_NOW_TYPES = {"half_time", "red_card"}  # stale an instant later: never held for a bundle
BUNDLE_WINDOW_MIN = 2.0
RESERVE_FROM_MINUTE = 75

Action = Literal["send", "hold", "skip"]


@dataclass
class Decision:
    action: Action
    reason: str
    threshold: int | None = None
    max_segments: int = 1


def threshold(ledger: Ledger) -> int:
    if not ledger.max_pings:
        return 50
    left = ledger.pings_left or 0
    return round(50 + 40 * (1 - left / ledger.max_pings))


def decide(fan: FanProfile, ledger: Ledger, moment: Moment, ranking: Ranking) -> Decision:
    score = ranking.score
    minute = moment.minute
    if fan.channel == "broadcast":
        if score >= OVERLAY_THRESHOLD:
            return Decision("send", f"overlay: score {score} >= {OVERLAY_THRESHOLD}")
        return Decision("skip", f"overlay: score {score} < {OVERLAY_THRESHOLD}")
    if ranking.skip:
        return Decision("skip", f"not about {fan.favorite_club or fan.favorite_player} (only_if_involved)")
    if fan.quiet_after_minute is not None and minute > fan.quiet_after_minute and moment.type != "goal":
        return Decision("skip", f"quiet after {fan.quiet_after_minute}'")
    typical = TYPICAL_KB.get(fan.channel, 1.0)
    if ledger.pings_left is not None and ledger.pings_left <= 0:
        return Decision("skip", "no pings left")
    if ledger.data_left_kb is not None and ledger.data_left_kb < typical:
        return Decision("skip", f"only {ledger.data_left_kb} KB left")

    reserve_ping = minute >= RESERVE_FROM_MINUTE and ledger.max_pings is not None
    reserve_kb = DIGEST_RESERVE_KB.get(fan.channel, 1.0) if minute >= RESERVE_FROM_MINUTE else 0.0
    if moment.type == "goal":
        if reserve_ping and (ledger.pings_left or 0) <= 1:
            return Decision("skip", "goal, but the last ping is reserved for the full-time digest")
        segs = 2 if fan.channel == "sms" and (ledger.pings_left is None or ledger.pings_left > 1) else 1
        return Decision("send", f"goal (score {score}): always send", max_segments=segs)

    th = threshold(ledger)
    if score < th:
        pings = "" if ledger.max_pings is None else f", {ledger.pings_left} of {ledger.max_pings} pings left"
        return Decision("skip", f"score {score} < threshold {th}{pings}", th)
    if ledger.max_pings is not None:
        keep = 2 if ledger.max_pings > 3 else 1
        if (ledger.pings_left or 0) <= keep:
            saved = "a goal and the full-time digest" if keep == 2 else "the full-time digest"
            return Decision(
                "skip", f"score {score} passes, but the last {keep} ping(s) are kept for {saved}", th
            )
    if ledger.data_left_kb is not None and ledger.data_left_kb - typical < reserve_kb:
        return Decision("skip", f"keeping {reserve_kb} KB for the full-time digest", th)
    if score >= SEND_NOW_SCORE or moment.type in SEND_NOW_TYPES:
        return Decision("send", f"score {score} >= threshold {th}: send now", th)
    return Decision("hold", f"score {score} >= threshold {th}: holding up to 2 min to bundle", th)
