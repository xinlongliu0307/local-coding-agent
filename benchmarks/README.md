# Benchmarks

Each task under `tasks/` is a directory containing:

- `task.json` — the brief given to the agent, the task name, and the
  expected difficulty.
- `workspace/` — the starting files. The runner copies this directory to a
  temporary location before each run, so the originals are never modified.
- `check.py` — a script run inside the workspace after the agent finishes.
  Exit code 0 means the task is scored as a pass; any other exit code is a
  fail. Checks assert on file content as well as behaviour wherever both
  matter, following the project's file-content-over-diff principle.

Run all tasks with:

    .venv/bin/python -m benchmarks.run

Results are appended to `benchmarks/results.jsonl`, one JSON object per
task per run, so successive runs (for example with different models) are
comparable.
