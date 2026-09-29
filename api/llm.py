"""The only module that knows which LLM provider the API uses.

To switch providers, implement `LLM.complete_json` for the new one and build it
in `create_llm`; nothing else changes.
"""
from __future__ import annotations

import json
from typing import Protocol

from api.settings import Settings

Message = dict[str, str]  # {"role": "system" | "user" | "assistant", "content": ...}


class LLMError(RuntimeError):
    """The provider failed or returned something that is not a JSON object."""


class LLM(Protocol):
    def complete_json(self, messages: list[Message]) -> dict:
        """Send a conversation and return the reply parsed as a JSON object."""


class OpenAILLM:
    def __init__(self, api_key: str, model: str, timeout: float, client=None):
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, timeout=timeout, max_retries=1)
        self._client = client
        self.model = model

    def complete_json(self, messages: list[Message]) -> dict:
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or ""
        except Exception as error:  # the SDK raises many error types; the caller only needs one
            raise LLMError(f"The language model request failed: {type(error).__name__}") from error
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as error:
            raise LLMError("The language model did not return valid JSON.") from error
        if not isinstance(parsed, dict):
            raise LLMError("The language model did not return a JSON object.")
        return parsed


def create_llm(settings: Settings) -> LLM | None:
    if not settings.llm_configured:
        return None
    return OpenAILLM(
        api_key=settings.openai_api_key.get_secret_value(),
        model=settings.llm_model,
        timeout=settings.llm_timeout_seconds,
    )
