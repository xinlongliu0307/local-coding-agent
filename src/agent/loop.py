"""The core ReAct loop: reason, act via tools, observe, repeat."""

from __future__ import annotations

import json
import re
from typing import Any, Callable

from agent.approval import (
    ApprovalSession,
    batch_console_approver,
    console_approver,
)
from agent.mode import Mode, cadence_for
from agent.model import ModelClient
from agent.tools.registry import TOOL_FUNCTIONS, TOOL_SCHEMAS

from agent.approval import ApprovalSession
from agent.mode import Mode


SYSTEM_PROMPT = (
    "You are a coding assistant operating in a command-line environment. "
    "You have access to tools that let you inspect and act on the user's "
    "project. When a task requires information you do not have, call the "
    "appropriate tool rather than guessing. Some tools change the filesystem "
    "and require user approval; if an action is declined, do not retry it "
    "without changing your approach. When you have enough information to "
    "answer or have completed the task, respond with plain text and do not "
    "call further tools."
)

MAX_ITERATIONS = 10


def run_task(
    task: str,
    mode: Mode = Mode.CAREFUL,
    model: ModelClient | None = None,
    session: ApprovalSession | None = None,
    verbose: bool = True,
) -> str:
    """Run a single task through the ReAct loop and return the final answer.

    The mode is declared at the start of the task and determines the approval
    cadence. Careful mode approves each mutating action individually; routine
    mode approves mutating actions once for the whole task. A custom approval
    session may be supplied to override the default console-based approvers,
    which is used in testing.
    """
    client = model or ModelClient()
    approval = session or ApprovalSession(
        mode=mode,
        per_call_approver=console_approver,
        batch_approver=batch_console_approver,
    )

    if verbose:
        print(f"Operating mode: {approval.mode.value}")
        print(f"Approval cadence: {cadence_for(approval.mode)}")

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
        if not tool_calls:
            embedded = _extract_embedded_tool_calls(message.get("content", ""))
            if embedded:
                tool_calls = embedded

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

            if not approval.is_approved(name, arguments):
                result = (
                    f"The user declined to approve the '{name}' action. "
                    "It was not performed."
                )
                if verbose:
                    print(result)
            else:
                result = _dispatch_tool(name, arguments)
                if verbose:
                    print(f"Tool result:\n{result}")

            messages.append({"role": "tool", "content": result})

    return (
        "The task did not complete within the iteration limit. "
        "The conversation may require a higher limit or a clearer task."
    )


def _extract_embedded_tool_calls(content: str) -> list[dict[str, Any]]:
    """Detect one or more tool-call JSON objects embedded in text content.

    Smaller models sometimes emit tool calls as JSON in the content field
    rather than using the structured tool_calls field, and may emit several
    such objects in a single response. This finds every top-level JSON object
    in the content, parses each, and returns those that name a known tool,
    normalised into the structured tool-call shape. Returns an empty list if
    none are found.
    """
    if not content:
        return []

    calls: list[dict[str, Any]] = []
    for match in re.finditer(r"\{(?:[^{}]|\{[^{}]*\})*\}", content):
        candidate = match.group(0)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            continue
        name = parsed.get("name")
        if not isinstance(name, str) or name not in TOOL_FUNCTIONS:
            continue
        arguments = parsed.get("arguments", {})
        calls.append({"function": {"name": name, "arguments": arguments}})
    return calls


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

def test_loop_detects_multiple_tool_calls_embedded_in_content(tmp_path):
    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.txt"
    content = (
        f'{{"name": "write_file", "arguments": {{"path": "{file_a}", '
        f'"content": "a"}}}}\n'
        f'{{"name": "write_file", "arguments": {{"path": "{file_b}", '
        f'"content": "b"}}}}'
    )
    fake = FakeModelClient(
        [
            {"content": content, "tool_calls": None},
            {"content": "Both files created.", "tool_calls": None},
        ]
    )
    session = ApprovalSession(Mode.CAREFUL, lambda n, a: True, lambda: True)
    result = run_task(
        "Create two files.", model=fake, session=session, verbose=False
    )
    assert result == "Both files created."
    assert file_a.read_text() == "a"
    assert file_b.read_text() == "b"
