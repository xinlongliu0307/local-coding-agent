"""Thin wrapper around the Ollama client for local model inference."""

from __future__ import annotations

import ollama


DEFAULT_MODEL = "qwen2.5-coder:7b"


class ModelClient:
    """A minimal client for sending chat messages to a local Ollama model."""

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.model = model

    def chat(self, messages: list[dict[str, str]]) -> str:
        """Send a list of chat messages and return the model's text reply.

        Each message is a dict with 'role' and 'content' keys, following the
        standard chat format. The reply is returned as a plain string.
        """
        response = ollama.chat(model=self.model, messages=messages)
        return response["message"]["content"]
