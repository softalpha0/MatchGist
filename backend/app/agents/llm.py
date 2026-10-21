"""Model plumbing for the language agents (Microsoft Agent Framework).

Backends, picked from the environment (see ``.env.example``):
  * Azure OpenAI in Microsoft Foundry with an API key: ``AZURE_OPENAI_ENDPOINT`` + ``AZURE_OPENAI_API_KEY``
    + ``AZURE_OPENAI_DEPLOYMENT_FAST`` (Agent Framework ``OpenAIChatCompletionClient``).
  * A Foundry project with Entra ID: ``AZURE_AI_PROJECT_ENDPOINT`` (``FoundryChatClient`` +
    ``DefaultAzureCredential``; needs the ``foundry`` extra).
  * Any OpenAI-compatible endpoint (e.g. a free tier): ``MATCHGIST_LLM_BASE_URL`` + ``MATCHGIST_LLM_API_KEY``
    + ``MATCHGIST_LLM_MODEL`` (same ``OpenAIChatCompletionClient``, pointed at ``base_url``).
  * Offline: no keys, or ``MATCHGIST_OFFLINE=1``. A deterministic Agent Framework chat client that
    renders the multilingual templates, so the same agents and workflow run for free.

Every call goes through :func:`call_agent`: 8 s timeout, 2 retries with backoff, then a fallback.
:class:`CallCap` optionally caps model calls per minute and per day, so a free tier's quota or a public demo
link can't run away; calls over the cap go straight to the templates.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections import deque
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from agent_framework import Agent, BaseChatClient, ChatResponse, Message

log = logging.getLogger(__name__)
logging.getLogger("agent_framework").setLevel(logging.ERROR)  # offline client has no tool layer; expected

OFFLINE_LABEL = "offline-templates"


@dataclass(frozen=True)
class LLMSettings:
    openai_endpoint: str | None
    openai_key: str | None
    deployment_fast: str
    deployment_digest: str | None
    api_version: str
    project_endpoint: str | None
    offline: bool
    timeout_s: float = 8.0
    retries: int = 2
    backoff_s: float = 0.5
    compat_base_url: str | None = None
    compat_key: str | None = None
    compat_model: str | None = None
    calls_per_minute: int = 0  # 0 = no cap
    calls_per_day: int = 0

    @classmethod
    def from_env(cls) -> LLMSettings:
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:  # pragma: no cover
            pass
        env = os.getenv
        return cls(
            openai_endpoint=env("AZURE_OPENAI_ENDPOINT") or None,
            openai_key=env("AZURE_OPENAI_API_KEY") or None,
            deployment_fast=env("AZURE_OPENAI_DEPLOYMENT_FAST") or "gpt-4o-mini",
            deployment_digest=env("AZURE_OPENAI_DEPLOYMENT_DIGEST") or None,
            api_version=env("AZURE_OPENAI_API_VERSION") or "2024-10-21",
            project_endpoint=env("AZURE_AI_PROJECT_ENDPOINT") or None,
            offline=(env("MATCHGIST_OFFLINE") or "").lower() in {"1", "true", "yes"},
            timeout_s=float(env("MATCHGIST_LLM_TIMEOUT") or 8),
            compat_base_url=env("MATCHGIST_LLM_BASE_URL") or None,
            compat_key=env("MATCHGIST_LLM_API_KEY") or None,
            compat_model=env("MATCHGIST_LLM_MODEL") or None,
            calls_per_minute=int(env("MATCHGIST_LLM_CALLS_PER_MINUTE") or 0),
            calls_per_day=int(env("MATCHGIST_LLM_CALLS_PER_DAY") or 0),
        )

    @property
    def mode(self) -> str:
        if self.offline:
            return "offline"
        if self.openai_endpoint and self.openai_key:
            return "azure-openai"
        if self.project_endpoint:
            return "foundry"
        if self.compat_base_url and self.compat_key and self.compat_model:
            return "openai-compatible"
        return "offline"


class CallCap:
    """Sliding one-minute window plus a daily count, shared by every match in the process.

    Free tiers reject bursts with 429s; refusing locally instead means the template fallback answers at once,
    rather than after a timeout and two retries, so playback never stalls.
    """

    def __init__(self, per_minute: int = 0, per_day: int = 0, clock: Callable[[], float] = time.monotonic):
        self.per_minute = per_minute
        self.per_day = per_day
        self.clock = clock
        self._recent: deque[float] = deque()
        self._day = time.strftime("%Y-%m-%d", time.gmtime())
        self._today = 0

    def take(self) -> str | None:
        """Reserve one call. Returns None if allowed, otherwise why not."""
        day = time.strftime("%Y-%m-%d", time.gmtime())
        if day != self._day:
            self._day, self._today = day, 0
        if self.per_day and self._today >= self.per_day:
            return f"daily model-call cap reached ({self.per_day})"
        now = self.clock()
        while self._recent and now - self._recent[0] >= 60:
            self._recent.popleft()
        if self.per_minute and len(self._recent) >= self.per_minute:
            return f"model-call cap reached ({self.per_minute}/min)"
        self._recent.append(now)
        self._today += 1
        return None


_CAPS: dict[tuple[int, int], CallCap] = {}


def shared_cap(settings: LLMSettings) -> CallCap:
    """One cap per process (per setting), so concurrent demo matches share the provider's quota."""
    key = (settings.calls_per_minute, settings.calls_per_day)
    if key not in _CAPS:
        _CAPS[key] = CallCap(*key)
    return _CAPS[key]


# ------------------------------------------------------------------ offline backend
OfflineHandler = Callable[[dict[str, Any]], str]
OFFLINE_HANDLERS: dict[str, OfflineHandler] = {}


def offline_handler(task: str) -> Callable[[OfflineHandler], OfflineHandler]:
    def register(fn: OfflineHandler) -> OfflineHandler:
        OFFLINE_HANDLERS[task] = fn
        return fn

    return register


def task_message(task: str, **payload: Any) -> str:
    """The JSON envelope every agent receives (and the offline client parses)."""
    return json.dumps({"task": task, **payload}, ensure_ascii=False, default=str)


def _parse_task(messages: Sequence[Message]) -> dict[str, Any]:
    for m in reversed(messages):
        text = m.text or ""
        start = text.find("{")
        if start >= 0:
            try:
                return json.loads(text[start:])
            except json.JSONDecodeError:
                continue
    return {}


class OfflineChatClient(BaseChatClient):
    """Deterministic Agent Framework chat client: same agents, no model, no cost."""

    def _inner_get_response(self, *, messages: Sequence[Message], stream: bool, options: Any, **kwargs: Any):
        if stream:
            raise NotImplementedError("offline backend does not stream")

        async def respond() -> ChatResponse:
            task = _parse_task(messages)
            handler = OFFLINE_HANDLERS.get(task.get("task", ""))
            text = handler(task) if handler else ""
            return ChatResponse(messages=Message("assistant", [text]), model=OFFLINE_LABEL)

        return respond()


# ------------------------------------------------------------------ client factory
def make_clients(settings: LLMSettings) -> tuple[Any, Any, str]:
    """Return ``(fast_client, digest_client, label)``. Falls back to offline if a backend can't start."""
    try:
        if settings.mode == "azure-openai":
            from agent_framework.openai import OpenAIChatCompletionClient

            def client(deployment: str) -> Any:
                return OpenAIChatCompletionClient(
                    model=deployment,
                    api_key=settings.openai_key,
                    azure_endpoint=settings.openai_endpoint,
                    api_version=settings.api_version,
                )

            fast = client(settings.deployment_fast)
            digest = client(settings.deployment_digest) if settings.deployment_digest else fast
            return fast, digest, f"azure-openai:{settings.deployment_fast}"
        if settings.mode == "foundry":
            from agent_framework.foundry import FoundryChatClient
            from azure.identity.aio import DefaultAzureCredential

            cred = DefaultAzureCredential()
            fast = FoundryChatClient(
                project_endpoint=settings.project_endpoint, model=settings.deployment_fast, credential=cred
            )
            digest = (
                FoundryChatClient(
                    project_endpoint=settings.project_endpoint,
                    model=settings.deployment_digest,
                    credential=cred,
                )
                if settings.deployment_digest
                else fast
            )
            return fast, digest, f"foundry:{settings.deployment_fast}"
        if settings.mode == "openai-compatible":
            from agent_framework.openai import OpenAIChatCompletionClient

            fast = OpenAIChatCompletionClient(
                model=settings.compat_model, api_key=settings.compat_key, base_url=settings.compat_base_url
            )
            return fast, fast, f"openai-compatible:{settings.compat_model}"
    except Exception as exc:  # missing package or bad config: keep the feed alive
        log.warning("model backend unavailable (%s); using offline templates", exc)
    offline = OfflineChatClient()
    return offline, offline, OFFLINE_LABEL


# ------------------------------------------------------------------ supervised calls
@dataclass
class AgentResult:
    text: str
    ok: bool
    attempts: int
    latency_ms: int
    error: str | None = None


async def call_agent(
    agent: Agent,
    message: str,
    *,
    timeout_s: float = 8.0,
    retries: int = 2,
    backoff_s: float = 0.5,
    validate: Callable[[str], bool] | None = None,
) -> AgentResult:
    """Run an agent with a timeout and retries. ``ok`` is False when every attempt failed."""
    start = time.perf_counter()
    error: str | None = None
    for attempt in range(1, retries + 2):
        try:
            resp = await asyncio.wait_for(agent.run(message), timeout=timeout_s)
            text = (resp.text or "").strip()
            if text and (validate is None or validate(text)):
                return AgentResult(text, True, attempt, int((time.perf_counter() - start) * 1000))
            error = "empty or unusable output"
        except TimeoutError:
            error = f"timeout after {timeout_s:.0f}s"
        except Exception as exc:  # any transport/model error is retried, then falls back
            error = f"{type(exc).__name__}: {str(exc)[:160]}"
        if attempt <= retries:
            await asyncio.sleep(backoff_s * attempt)
    return AgentResult("", False, retries + 1, int((time.perf_counter() - start) * 1000), error)


def parse_json_reply(text: str) -> dict[str, Any] | None:
    """Pull the first JSON object out of a model reply (models sometimes wrap it in prose or fences)."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None
