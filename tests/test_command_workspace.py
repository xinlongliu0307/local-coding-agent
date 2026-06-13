"""Tests that the command tool runs within the workspace root."""

from __future__ import annotations

import os

from agent.tools.run_command import run_command
from agent.workspace import set_workspace_root


def test_command_runs_in_workspace_root(tmp_path):
    marker = tmp_path / "here.txt"
    marker.write_text("present")
    set_workspace_root(str(tmp_path))
    try:
        # 'ls' run from the workspace root should see the file created there,
        # regardless of the process's own working directory.
        result = run_command("ls")
        assert "here.txt" in result
    finally:
        set_workspace_root(None)


def test_command_pwd_reports_workspace_root(tmp_path):
    set_workspace_root(str(tmp_path))
    try:
        result = run_command("pwd")
        assert os.path.realpath(str(tmp_path)) in result
    finally:
        set_workspace_root(None)


def test_command_without_root_uses_working_directory(tmp_path):
    # With no workspace root set, the command runs from the process working
    # directory, preserving prior behaviour.
    set_workspace_root(None)
    result = run_command("pwd")
    assert os.path.realpath(os.getcwd()) in result


def test_relative_path_resolves_within_workspace(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "value.txt").write_text("scoped")
    set_workspace_root(str(tmp_path))
    try:
        result = run_command("cat data/value.txt")
        assert "scoped" in result
    finally:
        set_workspace_root(None)
