"""Model backends for the language agents.

``FoundryChatClient`` (Microsoft Foundry, via Agent Framework) is used when a
project endpoint and model deployment are configured. Otherwise the agents run
on ``OfflineChatClient``: a deterministic Agent Framework chat client that
renders the multilingual templates, so the whole multi-agent pipeline (same
agents, same workflow, same verifier) runs for free with no keys.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from typing import Any

from agent_framework import BaseChatClient, ChatResponse, Message

from touchline.agents import templates
from touchline.config import Settings

log = logging.getLogger(__name__)
# Agent Framework warns that the offline client has no function-calling layer; that is expected.
logging.getLogger("agent_framework").setLevel(logging.ERROR)

OFFLINE_MODEL = "touchline-offline-templates"


def parse_task(messages: Sequence[Message]) -> dict[str, Any]:
    """Agents send a JSON task envelope as the last user message."""
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
    """Deterministic stand-in for a hosted model."""

    def _inner_get_response(self, *, messages: Sequence[Message], stream: bool, options: Any, **kwargs: Any):
        if stream:
            raise NotImplementedError("offline backend does not stream")

        async def respond() -> ChatResponse:
            task = parse_task(messages)
            text = self.complete(task)
            return ChatResponse(messages=Message("assistant", [text]), model=OFFLINE_MODEL)

        return respond()

    @staticmethod
    def complete(task: dict[str, Any]) -> str:
        kind = task.get("kind", "")
        facts = task.get("facts", {})
        profile = task.get("profile", {})
        lang = profile.get("language", "en")
        mode = profile.get("mode", "analyst")
        match task.get("task"):
            case "explain":
                return templates.explain(kind, facts, "en", "analyst")
            case "personalize":
                return templates.explain(kind, facts, lang, mode)
            case "recap":
                return templates.explain(kind, facts, lang, mode)
        return ""


_shared: dict[tuple[str, str], Any] = {}


def make_client(settings: Settings) -> tuple[Any, str]:
    """Return ``(chat_client, model_label)``.

    One Foundry client (and credential) is shared by every session in the process; the client is
    safe for concurrent async calls on one event loop.
    """
    if settings.use_foundry:
        assert settings.foundry_endpoint and settings.foundry_model
        key = (settings.foundry_endpoint, settings.foundry_model)
        if key in _shared:
            return _shared[key], f"foundry:{settings.foundry_model}"
        try:
            from agent_framework.foundry import FoundryChatClient
            from azure.identity.aio import DefaultAzureCredential

            client = FoundryChatClient(
                project_endpoint=settings.foundry_endpoint,
                model=settings.foundry_model,
                credential=DefaultAzureCredential(),
            )
            _shared[key] = client
            return client, f"foundry:{settings.foundry_model}"
        except Exception as exc:  # missing extra, bad config: keep the demo alive
            log.warning("Foundry unavailable (%s); falling back to offline backend", exc)
    return OfflineChatClient(), OFFLINE_MODEL
