"""Command-line entry point for running a task through the agent loop."""

from __future__ import annotations

import sys

from agent.loop import run_task
from agent.mode import Mode


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python -m agent "your task here" [careful|routine]')
        sys.exit(1)

    task = sys.argv[1]

    mode = Mode.CAREFUL
    if len(sys.argv) >= 3:
        requested = sys.argv[2].strip().lower()
        try:
            mode = Mode(requested)
        except ValueError:
            print(f"Unknown mode '{requested}'. Use 'careful' or 'routine'.")
            sys.exit(1)

    answer = run_task(task, mode=mode)
    print("\n=== Final Answer ===")
    print(answer)


if __name__ == "__main__":
    main()
