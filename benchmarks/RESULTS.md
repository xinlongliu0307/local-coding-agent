# Benchmark Results

This document records the outcomes of running the evaluation harness in
`benchmarks/` against two locally served open-weights models. It is a
factual summary of the recorded runs in the local results log; the two
findings below are the substantive outcome of the exercise.

## Method

Each of the three benchmark tasks (one scaffolding, one modification, one
diagnostic) was run repeatedly against each model during development. Every
run executes the agent in an isolated temporary workspace under an
auto-approving session, then scores the result with a check script whose
exit code determines pass or fail. Checks assert on file content as well as
behaviour wherever both matter, following the project's
file-content-over-diff principle. Each run appends one JSON record per task
to a local results log, including the agent's final answer, so that failures
can be diagnosed from what the model actually produced rather than from the
verdict alone.

Two models were compared, both served locally via Ollama:

- `qwen2.5-coder:7b` — the development model (roughly 4.7 GB).
- `qwen2.5-coder:32b` — the larger comparison model (roughly 20 GB).

## Aggregate pass rates

Pass rates below are taken from the full recorded history across all runs
during development, not from any single run.

| Task kind     | qwen2.5-coder:7b | qwen2.5-coder:32b |
| ------------- | ---------------- | ----------------- |
| scaffolding   | 9/9              | 2/2               |
| modification  | 1/9              | 2/2               |
| diagnostic    | 6/9              | 1/2               |
| **total**     | 16/27            | 5/6               |

Approximate per-task wall-clock times varied with system load and with
whether a model was already resident in memory; the larger model was
consistently slower per task, which is expected at the parameter difference
involved. Timing figures in the results log should be read as indicative
rather than precise, because concurrent runs and model residency affected
them.

## Finding one: the modification task is a model-capability gradient

The scaffolding task passed reliably for both models from the outset. The
modification task did not. It asks the agent to make a clean, minimal edit
to an existing file, and its check rejects both wrong behaviour and leftover
or duplicated lines.

The smaller model failed this task repeatedly during development, and the
recorded final answers show the failure evolving as the agent was improved:

- Initially, the model emitted its edit request as JSON in the message
  content rather than guessing the file's contents, supplying an
  `old_string` that did not exist in the file. The edit tool's uniqueness
  safeguard correctly refused, and no edit was made. This vindicated the
  read-before-edit mandate in the design requirements: the model was
  hallucinating file contents instead of reading them.
- After the refusal message was changed to inject the file's actual
  contents back to the model, the behaviour changed: the model began
  reading the real file and attempting a genuine edit, but produced a minor
  syntactic error (a stray character outside a string literal), causing a
  syntax error rather than a wrong value. This was a markedly better
  failure, and evidence that the agent's machinery was working: the
  limitation had narrowed to the model's edit precision.

The larger model produced clean, correct edits on this task. The honest
reading of the full history is therefore that the smaller model passes the
modification task only intermittently, while the larger model passes it
reliably; the gap is one of model capability at the edit-precision level,
closed by scale rather than by prompt engineering.

## Finding two: a benchmark ambiguity surfaced as a model failure

The more valuable finding concerns the evaluation itself. The diagnostic
task originally asked the agent to fix a `variance` function so that
`variance([1, 2, 3])` was "close to 0.6667," which is the population
variance (dividing by N). On one comparison run the larger model failed
this task, returning 1.0.

The recorded final answers showed that the model had not failed to edit at
all; it had computed the sample variance (dividing by N − 1, Bessel's
correction) instead. Both values are correct variances under different
conventions. The task brief was ambiguous at the domain-contract level: it
named a target value without naming the convention, and a model reaching
for the more common sample-variance default was not wrong so much as
resolving an underspecification differently than the check did.

The brief was then tightened to name the population convention explicitly
and to instruct division by `len(values)`. After this change, the
diagnostic task passed for both models. No model behaviour changed between
the failing and passing runs; only the specification changed.

This is the harness doing exactly what a good evaluation should: revealing
not only how the models perform but where the evaluation itself was
underspecified. It mirrors, in the project's own test domain, the
domain-contract underspecification lesson recorded in the design
requirements — that a wrong convention assumption can produce plausible but
unintended output, and that the cost of silent assumption-making is highest
in scientific computing.

## Reproducing

From the repository root, with Ollama serving the desired model:

    .venv/bin/python -m benchmarks.run                    # default model
    .venv/bin/python -m benchmarks.run qwen2.5-coder:32b  # a named model

Results append to `benchmarks/results.jsonl`, which is intentionally not
tracked in version control, as it is a local measurement log.
