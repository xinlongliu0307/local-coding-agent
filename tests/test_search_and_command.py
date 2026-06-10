"""Tests for the search tool and the gated command-execution tool."""

from __future__ import annotations

from typing import Any

from agent.approval import ApprovalSession
from agent.loop import run_task
from agent.mode import Mode
from agent.tools.run_command import run_command
from agent.tools.search_files import search_files


class FakeModelClient:
    def __init__(self, scripted_responses: list[dict[str, Any]]) -> None:
        self._responses = list(scripted_responses)
        self.calls = 0

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self.calls += 1
        return self._responses.pop(0)


def test_search_finds_match_with_path_and_line(tmp_path):
    target = tmp_path / "notes.txt"
    target.write_text("alpha\nneedle here\nomega\n")
    result = search_files("needle", str(tmp_path))
    assert "notes.txt:2" in result
    assert "needle here" in result


def test_search_reports_no_matches(tmp_path):
    (tmp_path / "a.txt").write_text("nothing relevant\n")
    result = search_files("absent-token", str(tmp_path))
    assert "No matches" in result


def test_search_rejects_empty_query(tmp_path):
    assert "Error" in search_files("", str(tmp_path))


def test_search_caps_results(tmp_path):
    lines = "\n".join("needle" for _ in range(60))
    (tmp_path / "big.txt").write_text(lines + "\n")
    result = search_files("needle", str(tmp_path))
    assert "stopped after 50 matches" in result


def test_run_command_reports_exit_code_and_stdout():
    result = run_command("echo hello")
    assert "exit code: 0" in result
    assert "hello" in result


def test_run_command_reports_failure_exit_code():
    result = run_command("false")
    assert "exit code: 1" in result


def test_run_command_rejects_empty_command():
    assert "Error" in run_command("   ")


def test_loop_blocks_command_when_denied(tmp_path):
    target = tmp_path / "must_not_exist.txt"
    fake = FakeModelClient(
        [
            {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "run_command",
                            "arguments": {"command": f"touch {target}"},
                        }
                    }
                ],
            },
            {"content": "Understood, not running it.", "tool_calls": None},
        ]
    )
    session = ApprovalSession(Mode.CAREFUL, lambda n, a: False, lambda: False)
    result = run_task(
        "Touch a file.",
        model=fake,
        session=session,
        verbose=False,
        include_summary=False,
        enable_snapshot=False,
        declare_reading_order=False,
    )
    assert result == "Understood, not running it."
    assert not target.exists()
