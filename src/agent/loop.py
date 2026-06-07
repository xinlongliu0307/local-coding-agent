"""The core ReAct loop: reason, act via tools, observe, repeat."""

from __future__ import annotations

import json
import re
from typing import Any

from agent.approval import (
    ApprovalSession,
    batch_console_approver,
    console_approver,
)
from agent.clarify import assess_brief
from agent.mode import CLARIFYING_MODES, Mode, cadence_for
from agent.model import ModelClient
from agent.record import TaskRecord
from agent.summary import build_summary
from agent.tools.registry import TOOL_FUNCTIONS, TOOL_SCHEMAS
from agent.snapshot import prune_old_snapshots, take_snapshot


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
    include_summary: bool = True,
    enable_snapshot: bool = True,
) -> str:
    """Run a single task through the ReAct loop and return the final answer.

    A task record is maintained throughout, and unless include_summary is
    False, a structured self-summary of files created and modified, tools
    invoked, and actions declined is appended to the returned result. When
    the mode triggers clarification and the brief is judged underspecified,
    the loop returns clarifying questions without performing work.
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

    if approval.mode in CLARIFYING_MODES:
        needs_clarification, questions = assess_brief(task, client)
        if needs_clarification and questions:
            return _format_clarifying_questions(questions)

    record = TaskRecord()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    final_text = ""
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
            break

        for call in tool_calls:
            function = call.get("function", {})
            name = function.get("name", "")
            raw_arguments = function.get("arguments", {})
            arguments = _coerce_arguments(raw_arguments)

            if verbose:
                print(f"Model requested tool: {name}({arguments})")

            existed_before = record.note_pre_state(name, arguments)
            approved = approval.is_approved(name, arguments)

            if not approved:
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

            record.add_event(name, arguments, approved, result, existed_before)
            messages.append({"role": "tool", "content": result})
    else:
        final_text = (
            "The task did not complete within the iteration limit. "
            "The conversation may require a higher limit or a clearer task."
        )

    if enable_snapshot:
        changed = record.created_files + record.modified_files
        snapshot_dir = take_snapshot(changed)
        prune_old_snapshots()
        if verbose and snapshot_dir is not None:
            print(f"\nSnapshot of changed files saved to: {snapshot_dir}")

    if include_summary:
        return final_text + "\n" + build_summary(record)
    return final_text


def _format_clarifying_questions(questions: list[str]) -> str:
    """Format clarifying questions for presentation to the user."""
    lines = [
        "Before proceeding, the task needs clarification on the following:",
    ]
    for index, question in enumerate(questions, start=1):
        lines.append(f"{index}. {question}")
    lines.append(
        "Please re-run the task with these details included in the brief."
    )
    return "\n".join(lines)


def _extract_embedded_tool_calls(content: str) -> list[dict[str, Any]]:
    """Detect one or more tool-call JSON objects embedded in text content."""
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
