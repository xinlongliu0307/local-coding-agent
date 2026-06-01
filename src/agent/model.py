"""Thin wrapper around the Ollama client for local model inference."""

from __future__ import annotations

from typing import Any

import ollama


DEFAULT_MODEL = "qwen2.5-coder:7b"


class ModelClient:
    """A minimal client for sending chat messages to a local Ollama model."""

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.model = model

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send chat messages and return the model's full response message.

        Each message is a dict with at least 'role' and 'content' keys. When
        a list of tool definitions is supplied, the model may respond with
        tool calls instead of, or in addition to, text content. The full
        message object is returned so that the caller can inspect both the
        text content and any tool calls the model has requested.
        """
        response = ollama.chat(
            model=self.model,
            messages=messages,
            tools=tools or [],
        )
        return response["message"]
