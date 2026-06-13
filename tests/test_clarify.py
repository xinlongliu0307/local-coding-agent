"""Tests for the clarifying-question protocol and ask mode."""

from __future__ import annotations

from typing import Any

from agent.approval import ApprovalSession
from agent.clarify import assess_brief
from agent.loop import run_task
from agent.mode import Mode


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


def test_assess_brief_reports_questions_when_underspecified():
    client = ScriptedClient(
        {
            "content": (
                '{"needs_clarification": true, '
                '"questions": ["What input format?", "What output format?"]}'
            )
        }
    )
    needs, questions = assess_brief("Process some data.", client)
    assert needs is True
    assert len(questions) == 2


def test_assess_brief_reports_no_questions_when_adequate():
    client = ScriptedClient(
        {"content": '{"needs_clarification": false, "questions": []}'}
    )
    needs, questions = assess_brief("A very detailed brief.", client)
    assert needs is False
    assert questions == []


def test_assess_brief_fails_safe_on_unparseable_response():
    client = ScriptedClient({"content": "I am not valid JSON at all."})
    needs, questions = assess_brief("Some brief.", client)
    assert needs is False
    assert questions == []


def test_assess_brief_caps_questions_at_five():
    many = ", ".join(f'"q{i}"' for i in range(8))
    client = ScriptedClient(
        {"content": f'{{"needs_clarification": true, "questions": [{many}]}}'}
    )
    needs, questions = assess_brief("Vague.", client)
    assert needs is True
    assert len(questions) == 5


def test_ask_mode_returns_questions_without_working():
    client = ScriptedClient(
        {
            "content": (
                '{"needs_clarification": true, '
                '"questions": ["What input format?"]}'
            )
        }
    )
    session = ApprovalSession(Mode.ASK, lambda n, a: True, lambda: True)
    result = run_task(
        "Process some data.", model=client, session=session, verbose=False
    )
    assert "clarification" in result.lower()
    assert "What input format?" in result
    assert client.calls == 1


def test_ask_mode_proceeds_when_brief_is_adequate(workspace):
    target = workspace / "out.txt"
    client = SequenceClient(
        [
            {"content": '{"needs_clarification": false, "questions": []}'},
            {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "write_file",
                            "arguments": {"path": str(target), "content": "x"},
                        }
                    }
                ],
            },
            {"content": "Done.", "tool_calls": None},
        ]
    )
    session = ApprovalSession(Mode.ASK, lambda n, a: True, lambda: True)
    result = run_task(
        "A fully specified task.",
        model=client,
        session=session,
        verbose=False,
        include_summary=False,
        declare_reading_order=False,
    )
    assert result == "Done."
    assert target.read_text() == "x"
