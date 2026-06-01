"""The core ReAct loop: reason, act via tools, observe, repeat."""

from __future__ import annotations

import json
import re
from typing import Any

from agent.model import ModelClient
from agent.tools.registry import TOOL_FUNCTIONS, TOOL_SCHEMAS


SYSTEM_PROMPT = (
    "You are a coding assistant operating in a command-line environment. "
    "You have access to tools that let you inspect and act on the user's "
    "project. When a task requires information you do not have, call the "
    "appropriate tool rather than guessing. When you have enough information "
    "to answer or have completed the task, respond with plain text and do "
    "not call further tools."
)

MAX_ITERATIONS = 10


def run_task(task: str, model: ModelClient | None = None, verbose: bool = True) -> str:
    """Run a single task through the ReAct loop and return the final answer."""
    client = model or ModelClient()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    for iteration in range(1, MAX_ITERATIONS + 1):
        if verbose:
            print(f"\n--- Iteration {iteration} ---")

        message = client.chat(messages, tools=TOOL_SCHEMAS)
        messages.append(message)

        tool_calls = message.get("tool_calls")

        # Fall back to detecting a tool call embedded in the text content,
        # which smaller models emit instead of using the structured field.
        if not tool_calls:
            embedded = _extract_embedded_tool_call(message.get("content", ""))
            if embedded is not None:
                tool_calls = [embedded]

        if not tool_calls:
            final_text = message.get("content", "")
            if verbose:
                print(f"Model produced final answer:\n{final_text}")
            return final_text

        for call in tool_calls:
            function = call.get("function", {})
            name = function.get("name", "")
            raw_arguments = function.get("arguments", {})
            arguments = _coerce_arguments(raw_arguments)

            if verbose:
                print(f"Model requested tool: {name}({arguments})")

            result = _dispatch_tool(name, arguments)

            if verbose:
                print(f"Tool result:\n{result}")

            messages.append({"role": "tool", "content": result})

    return (
        "The task did not complete within the iteration limit. "
        "The conversation may require a higher limit or a clearer task."
    )


def _extract_embedded_tool_call(content: str) -> dict[str, Any] | None:
    """Detect a tool-call JSON object embedded in the model's text content.

    Smaller models sometimes emit a tool call as JSON in the content field
    rather than using the structured tool_calls field. This attempts to
    parse such an object and normalise it into the same shape the structured
    field uses. Returns None if no valid tool-call object is found.
    """
    if not content:
        return None

    candidate = content.strip()

    # Strip Markdown code fences if the model wrapped the JSON in them.
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1)

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, dict):
        return None

    name = parsed.get("name")
    if not isinstance(name, str) or name not in TOOL_FUNCTIONS:
        return None

    arguments = parsed.get("arguments", {})
    return {"function": {"name": name, "arguments": arguments}}


def _coerce_arguments(raw: Any) -> dict[str, Any]:
    """Normalise tool-call arguments into a dictionary."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}


def _dispatch_tool(name: str, arguments: dict[str, Any]) -> str:
    """Execute the named tool with the given arguments and return its output."""
    function = TOOL_FUNCTIONS.get(name)
    if function is None:
        return f"Error: no tool named '{name}' is available."
    try:
        return function(**arguments)
    except TypeError as error:
        return f"Error calling '{name}': {error}"
