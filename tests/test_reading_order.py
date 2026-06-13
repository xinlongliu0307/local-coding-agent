"""Tests for task-type classification and reading-order declaration."""

from __future__ import annotations

from typing import Any

from agent.approval import ApprovalSession
from agent.loop import run_task
from agent.mode import Mode
from agent.reading_order import (
    TaskType,
    classify_task,
    reading_order_declaration,
)


class ScriptedClient:
    """A model client returning a fixed response to every chat call."""

    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls = 0

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self.calls += 1
        return self.response


class SequenceClient:
    """A model client returning a sequence of responses in order."""

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self._responses = list(responses)
        self.calls = 0

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self.calls += 1
        return self._responses.pop(0)


def test_classify_recognises_modification():
    client = ScriptedClient({"content": '{"task_type": "modification"}'})
    assert classify_task("Rename a function.", client) is TaskType.MODIFICATION


def test_classify_recognises_diagnostic():
    client = ScriptedClient({"content": '{"task_type": "diagnostic"}'})
    assert classify_task("Fix the wrong output.", client) is TaskType.DIAGNOSTIC


def test_classify_fails_safe_to_other_on_unparseable():
    client = ScriptedClient({"content": "not json"})
    assert classify_task("Something.", client) is TaskType.OTHER


def test_classify_fails_safe_to_other_on_unknown_type():
    client = ScriptedClient({"content": '{"task_type": "nonsense"}'})
    assert classify_task("Something.", client) is TaskType.OTHER


def test_declaration_renders_modification_order():
    declaration = reading_order_declaration(TaskType.MODIFICATION)
    assert declaration is not None
    assert "public interface" in declaration
    assert "entry point" in declaration


def test_declaration_renders_diagnostic_order():
    declaration = reading_order_declaration(TaskType.DIAGNOSTIC)
    assert declaration is not None
    assert "entry point" in declaration
    assert "data loading" in declaration


def test_declaration_is_none_for_other():
    assert reading_order_declaration(TaskType.OTHER) is None


def test_loop_proceeds_after_classifying_task(workspace):
    target = workspace / "code.py"
    target.write_text("greeting = 'hello'\n")
    client = SequenceClient(
        [
            {"content": '{"task_type": "modification"}'},
            {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "edit_file",
                            "arguments": {
                                "path": str(target),
                                "old_string": "greeting = 'hello'",
                                "new_string": "greeting = 'hi'",
                            },
                        }
                    }
                ],
            },
            {"content": "Updated.", "tool_calls": None},
        ]
    )
    session = ApprovalSession(Mode.CAREFUL, lambda n, a: True, lambda: True)
    result = run_task(
        "Change the greeting.",
        model=client,
        session=session,
        verbose=False,
        include_summary=False,
        enable_snapshot=False,
    )
    assert result == "Updated."
    assert target.read_text() == "greeting = 'hi'\n"
    assert client.calls == 3
