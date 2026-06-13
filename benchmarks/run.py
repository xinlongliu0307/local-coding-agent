"""Benchmark runner: execute each task in isolation and score the result."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime

from agent.approval import ApprovalSession
from agent.loop import run_task
from agent.mode import Mode
from agent.model import ModelClient, DEFAULT_MODEL


TASKS_DIR = os.path.join(os.path.dirname(__file__), "tasks")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "results.jsonl")
CHECK_TIMEOUT_SECONDS = 60


def discover_tasks() -> list[str]:
    """Return sorted task directory paths under the tasks directory."""
    entries = []
    for name in sorted(os.listdir(TASKS_DIR)):
        candidate = os.path.join(TASKS_DIR, name)
        if os.path.isdir(candidate) and os.path.isfile(
            os.path.join(candidate, "task.json")
        ):
            entries.append(candidate)
    return entries


def run_one(task_dir: str, model_name: str) -> dict:
    """Run a single task in a temporary workspace and return its result."""
    with open(os.path.join(task_dir, "task.json"), "r", encoding="utf-8") as f:
        spec = json.load(f)

    workspace_src = os.path.join(task_dir, "workspace")
    check_src = os.path.join(task_dir, "check.py")

    with tempfile.TemporaryDirectory() as workdir:
        if os.path.isdir(workspace_src):
            for entry in os.listdir(workspace_src):
                if entry == ".gitkeep":
                    continue
                shutil.copy2(
                    os.path.join(workspace_src, entry),
                    os.path.join(workdir, entry),
                )

        original_cwd = os.getcwd()
        os.chdir(workdir)
        started = time.time()
        final_answer = ""
        try:
            session = ApprovalSession(
                Mode.ROUTINE, lambda n, a: True, lambda: True
            )
            final_answer = run_task(
                spec["brief"],
                model=ModelClient(model=model_name),
                session=session,
                verbose=False,
                include_summary=False,
                enable_snapshot=False,
                declare_reading_order=False,
                workspace_root=workdir,
            )
            agent_error = None
        except Exception as error:  # noqa: BLE001 - record, do not crash
            agent_error = str(error)
        finally:
            elapsed = time.time() - started
            os.chdir(original_cwd)

        if agent_error is not None:
            passed, check_output = False, f"agent error: {agent_error}"
        else:
            shutil.copy2(check_src, os.path.join(workdir, "_check.py"))
            try:
                completed = subprocess.run(
                    [sys.executable, "_check.py"],
                    cwd=workdir,
                    capture_output=True,
                    text=True,
                    timeout=CHECK_TIMEOUT_SECONDS,
                )
                passed = completed.returncode == 0
                check_output = (completed.stdout + completed.stderr).strip()
            except subprocess.TimeoutExpired:
                passed, check_output = False, "check timed out"

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "task": spec["name"],
        "kind": spec.get("kind", "unknown"),
        "model": model_name,
        "passed": passed,
        "seconds": round(elapsed, 1),
        "check_output": check_output,
        "final_answer": (final_answer or "")[:500],
    }


def main() -> None:
    model_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    tasks = discover_tasks()
    if not tasks:
        print("No tasks found.")
        sys.exit(1)

    print(f"Running {len(tasks)} task(s) with model: {model_name}\n")
    results = []
    for task_dir in tasks:
        result = run_one(task_dir, model_name)
        results.append(result)
        status = "PASS" if result["passed"] else "FAIL"
        print(
            f"{status}  {result['task']}  ({result['kind']}, "
            f"{result['seconds']}s)"
        )
        if not result["passed"]:
            print(f"      {result['check_output']}")

    with open(RESULTS_PATH, "a", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result) + "\n")

    passed = sum(1 for r in results if r["passed"])
    print(f"\n{passed}/{len(results)} tasks passed. "
          f"Results appended to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
