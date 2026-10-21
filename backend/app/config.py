"""Settings read from the environment (see .env.example)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
MATCHES_DIR = REPO_ROOT / "matches"


@dataclass(frozen=True)
class Settings:
    sim_seed: int = int(os.getenv("SIM_SEED", "42"))
    sim_speed: float = float(os.getenv("SIM_SPEED", "10"))


def get_settings() -> Settings:
    return Settings()
