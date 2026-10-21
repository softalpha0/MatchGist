"""Per-fan delivery ledger: what was sent, data used, pings left, and which limit binds."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.fans.profiles import FanProfile

# Typical size of one message per channel (KB), used to say whether pings or data run out first.
TYPICAL_KB = {"sms": 0.2, "chat": 1.2, "voice": 24.0, "watch": 0.55, "push": 1.1, "broadcast": 0.0}
# What a full-time digest costs per channel (KB): reserved from the 75th minute.
DIGEST_RESERVE_KB = {"sms": 0.6, "chat": 1.6, "voice": 30.0, "watch": 0.6, "push": 1.2, "broadcast": 0.0}


class Delivery(BaseModel):
    """One message delivered to one fan (SPEC section 10.1)."""

    delivery_id: str
    fan_id: str
    kind: Literal["moment", "bundle", "digest", "overlay"]
    moment_ids: list[str]
    channel: str
    language: str
    match_clock: str
    text: str
    title: str | None = None
    value: str | None = None
    audio_url: str | None = None
    audio_seconds: float | None = None
    voice: str | None = None
    size_kb: float
    segments: int | None = None
    encoding: str | None = None
    budget_after: dict[str, Any] = Field(default_factory=dict)
    decision_reason: str
    fallback_used: bool = False
    attempts: int = 1
    overlay: dict[str, Any] | None = None


class Ledger(BaseModel):
    fan_id: str
    channel: str
    data_budget_kb: float | None
    max_pings: int | None
    data_used_kb: float = 0.0
    pings_used: int = 0
    deliveries: list[Delivery] = Field(default_factory=list)
    skipped: int = 0
    held: int = 0

    @classmethod
    def for_fan(cls, fan: FanProfile) -> Ledger:
        return cls(
            fan_id=fan.fan_id, channel=fan.channel, data_budget_kb=fan.data_budget_kb, max_pings=fan.max_pings
        )

    @property
    def data_left_kb(self) -> float | None:
        return None if self.data_budget_kb is None else round(self.data_budget_kb - self.data_used_kb, 2)

    @property
    def pings_left(self) -> int | None:
        return None if self.max_pings is None else self.max_pings - self.pings_used

    def binding_limit(self) -> str:
        """Which limit runs out first at this channel's typical message size: pings, data, or neither."""
        if self.channel == "broadcast":
            return "none"
        typical = TYPICAL_KB.get(self.channel, 1.0)
        by_data = None if self.data_left_kb is None else self.data_left_kb / typical
        by_pings = self.pings_left
        if by_data is None and by_pings is None:
            return "none"
        if by_data is None:
            return "pings"
        if by_pings is None:
            return "data"
        return "pings" if by_pings <= by_data else "data"

    def budget(self) -> dict[str, Any]:
        return {
            "data_kb_left": self.data_left_kb,
            "pings_left": self.pings_left,
            "data_used_kb": round(self.data_used_kb, 2),
            "pings_used": self.pings_used,
            "binding": self.binding_limit(),
        }

    def record(self, d: Delivery) -> Delivery:
        """Charge a delivery to the budget and store it (overlays are free and don't count as pings)."""
        if d.kind != "overlay":
            self.data_used_kb = round(self.data_used_kb + d.size_kb, 2)
            self.pings_used += 1
        d.budget_after = self.budget()
        self.deliveries.append(d)
        return d

    def summary(self) -> dict[str, Any]:
        return {
            **self.budget(),
            "fan_id": self.fan_id,
            "channel": self.channel,
            "deliveries": len(self.deliveries),
            "skipped": self.skipped,
            "data_budget_kb": self.data_budget_kb,
            "max_pings": self.max_pings,
        }
