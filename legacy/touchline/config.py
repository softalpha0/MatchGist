"""Runtime settings, read from the environment once at start-up."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # Microsoft Foundry (preferred). When both are set the language agents run on Foundry.
    foundry_endpoint: str | None = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
    foundry_model: str | None = os.getenv("FOUNDRY_MODEL")
    # Force the offline backend even when Foundry is configured (useful for demos and CI).
    force_offline: bool = _flag("TOUCHLINE_OFFLINE")
    # Guardrails on model usage for a public demo.
    llm_timeout_s: float = float(os.getenv("TOUCHLINE_LLM_TIMEOUT", "8"))
    llm_concurrency: int = int(os.getenv("TOUCHLINE_LLM_CONCURRENCY", "4"))
    llm_budget_per_session: int = int(os.getenv("TOUCHLINE_LLM_BUDGET", "120"))
    llm_min_importance: float = float(os.getenv("TOUCHLINE_LLM_MIN_IMPORTANCE", "0.45"))
    breaker_failures: int = int(os.getenv("TOUCHLINE_BREAKER_FAILURES", "3"))
    breaker_cooldown_s: float = float(os.getenv("TOUCHLINE_BREAKER_COOLDOWN", "30"))
    max_sessions: int = int(os.getenv("TOUCHLINE_MAX_SESSIONS", "40"))

    @property
    def use_foundry(self) -> bool:
        return bool(self.foundry_endpoint and self.foundry_model) and not self.force_offline


def get_settings() -> Settings:
    return Settings()
