"""Tests for the benchmark harness machinery."""

from __future__ import annotations

import json
import os
import subprocess
import sys

from benchmarks.run import discover_tasks, TASKS_DIR


def test_discover_finds_all_three_tasks():
    tasks = discover_tasks()
    names = [os.path.basename(t) for t in tasks]
    assert "01_scaffold" in names
    assert "02_modify" in names
    assert "03_diagnose" in names


def test_every_task_has_required_files():
    for task_dir in discover_tasks():
        assert os.path.isfile(os.path.join(task_dir, "task.json"))
        assert os.path.isfile(os.path.join(task_dir, "check.py"))
        spec_path = os.path.join(task_dir, "task.json")
        with open(spec_path, "r", encoding="utf-8") as handle:
            spec = json.load(handle)
        assert "name" in spec
        assert "brief" in spec


def test_modify_check_fails_on_unmodified_workspace(tmp_path):
    task_dir = os.path.join(TASKS_DIR, "02_modify")
    src = os.path.join(task_dir, "workspace", "greeter.py")
    check = os.path.join(task_dir, "check.py")
    with open(src, "r", encoding="utf-8") as handle:
        (tmp_path / "greeter.py").write_text(handle.read())
    with open(check, "r", encoding="utf-8") as handle:
        (tmp_path / "_check.py").write_text(handle.read())
    completed = subprocess.run(
        [sys.executable, "_check.py"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0


def test_diagnose_check_passes_on_fixed_workspace(tmp_path):
    fixed = (
        "def mean(values):\n"
        "    return sum(values) / len(values)\n\n\n"
        "def variance(values):\n"
        "    m = mean(values)\n"
        "    return sum((v - m) ** 2 for v in values) / len(values)\n"
    )
    (tmp_path / "stats.py").write_text(fixed)
    check = os.path.join(TASKS_DIR, "03_diagnose", "check.py")
    with open(check, "r", encoding="utf-8") as handle:
        (tmp_path / "_check.py").write_text(handle.read())
    completed = subprocess.run(
        [sys.executable, "_check.py"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
