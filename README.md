# local-coding-agent

A local, open-weights AI coding agent for general software engineering,
designed to run entirely on a personal laptop using language models
served via Ollama. The agent targets multi-file edits, refactoring, and
diagnostic work, with atmospheric sciences serving as the evaluation
domain during development.

## Status

The implementation roadmap is complete. The agent reads before
acting with a task-typed reading order, operates under a three-mode
approval disposition, clarifies underspecified briefs, edits under a
uniqueness safeguard, runs searches and shell commands behind an approval
gate, reports a factual self-summary, and snapshots every file it changes.
An evaluation harness scores it against scaffolding, modification, and
diagnostic tasks; see benchmarks/RESULTS.md.

## Design

The agent's design is grounded in four structured evaluation sessions
of OpenAI's Codex CLI conducted in late May 2026. The sessions covered
scaffolding work under a well-specified brief, behaviour under a
deliberately ambiguous brief, multi-file refactoring under constraint,
and diagnostic bug-hunting. The patterns observed in those sessions
are translated into mandatory and forbidden behaviours in
`docs/design/design-requirements.md`.

The design requirements document specifies the agent's intended
behaviour across eight sections, covering purpose and scope, mandatory
behaviours, forbidden behaviours, the three-mode disposition (ask,
prototype, commit), the clarifying-question protocol, verification
and self-reporting requirements, and the open questions that remain
for later resolution.

## Roadmap

The project followed a phased build plan, beginning with Phase Zero
(design and reference-agent evaluation) and proceeding through
implementation in Python using a ReAct loop against a local Ollama
server. The implemented phases delivered, in sequence: the model
client and a minimal loop; file inspection, writing, and a targeted
edit tool guarded by a uniqueness safeguard; an approval gate with a
three-mode disposition and mode-aware cadence; a clarifying-question
protocol for underspecified briefs; a factual self-summary; automatic
snapshotting with retention pruning; task-typed reading-order
declaration; search and approval-gated command execution; and an
evaluation harness. All implementation phases are complete and
committed.

Work beyond this point is open-ended extension rather than roadmap
completion. Candidate directions include broadening the benchmark set —
notably a second diagnostic task with an unambiguous bug, prompted by
the specification ambiguity recorded in `benchmarks/RESULTS.md` — and
resilience work for long multi-iteration conversations.

## Contributing

The implementation phases are complete, and the architecture is stable.
The project is a personal portfolio effort; issues and observations are
welcome, though the maintainer makes no commitment to accept external
contributions.

## License

Apache 2.0. See `LICENSE` for details.

## Benchmarks

A small evaluation harness lives in `benchmarks/`. It runs the agent against
three tasks — scaffolding, modification, and diagnostic — each scored by a
check script that asserts on file content as well as behaviour. Run all
tasks with:

    .venv/bin/python -m benchmarks.run

An optional model name may be supplied to compare models:

    .venv/bin/python -m benchmarks.run qwen2.5-coder:32b

Results are appended to `benchmarks/results.jsonl` (not tracked in version
control). A written comparison of two models, including two findings on
model capability and benchmark design, is in `benchmarks/RESULTS.md`.
