"""Command-line entry point for running a task through the agent loop."""

from __future__ import annotations

import sys

from agent.loop import run_task


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python -m agent "your task here"')
        sys.exit(1)
    task = sys.argv[1]
    answer = run_task(task)
    print("\n=== Final Answer ===")
    print(answer)


if __name__ == "__main__":
    main()
