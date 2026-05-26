# Agent Design Requirements

This document specifies the design requirements for the personal AI coding
agent to be built during Phase One onwards. It is the prescriptive
counterpart to `patterns-across-sessions.md`, which records the
observations from Phase Zero, Week One that motivate these requirements.

This file is a draft. Variation 3 will add a fourth session's evidence and
the synthesis weekend (31 May - 1 June) will produce the version that
becomes the first substantive commit to the public GitHub repository in
Phase Zero, Week Two.

## 1. Purpose and Scope

The agent is a general-purpose AI coding agent that runs entirely on a
local laptop using open-weights language models served via Ollama. It
targets general software engineering tasks: multi-file edits,
refactoring, running tests, and diagnostic work. It is not specialised
for any particular research domain; atmospheric sciences is used as the
evaluation domain because it lies outside the maintainer's active
research (Southern Ocean meanders and Antarctic sea-ice altimetry) and
therefore cannot become entangled with confidential data.

The agent's design is informed by a four-session evaluation of OpenAI's
Codex CLI conducted in late May 2026. The patterns observed in those
sessions are recorded in `patterns-across-sessions.md`; this document
translates those patterns into prescriptive design constraints. The
agent is intended to replicate Codex's strengths (forward-looking error
anticipation, careful read-before-write ordering, graceful sandbox
negotiation) while addressing its weaknesses (silent assumption-making
under ambiguity, path-of-least-resistance test fixes, Git-context
assumption regardless of repository state, incomplete self-summaries).

## 2. Mandatory Behaviours

The agent must exhibit the following behaviours by design rather than by
hope. Each is mandated by an observation from Phase Zero, Week One; the
source observation is cited.

1. Read existing code in the order public-API surface, then test
   contract, then refactor target, then build configuration, then
   entry point, when starting any task that modifies existing code.
   (Source: Variation 2's clean refactor.)

2. Pre-emptively declare expected dependencies, tools, and PATH
   locations before they are needed. (Source: Saturday's proactive
   pytest declaration.)

3. Use Python's `is` operator to test object identity, not just value
   equality, when verifying that a refactor has moved code between
   modules rather than duplicating it. (Source: Variation 2's
   boundary tests.)

4. Declare its mode (ask, prototype, or commit) explicitly at the
   start of each task, and justify the choice in one sentence.
   (Source: Variation 1's fresh-instance reflection.)

5. Detect Git repository presence explicitly at session start and
   surface the result in the opening environment summary, rather than
   issuing `git status` or `git log` reflexively. (Source: the Git-
   context assumption observed in all three sessions.)

6. When working in a scientific computing domain (identified by the
   presence of numpy, pandas, xarray, MetPy, or similar imports),
   require explicit declaration of units and data sources in the
   agent's preamble before any calculation is performed. (Source:
   Variation 1's fresh-instance reflection on domain-contract
   underspecification.)

7. Select reading order by task type. For refactor and modification
   tasks, read in the order public-API surface, then test contract,
   then implementation, then build configuration, then entry point.
   For diagnostic tasks, read in execution-pipeline order: entry
   point, then suspected calculation module, then data loading,
   then tests, then configuration. Declare the chosen order
   explicitly in the preamble. (Source: Variation 2's refactor
   reading order; Variation 3's diagnostic reading order.)

8. Articulate a confidence level for each proposed change in
   diagnostic work, stated before the verification step rather than
   after it. The confidence statement should be brief (one or two
   sentences) and should give the user a basis for trusting or
   questioning the fix before tests are run. (Source: Variation 3's
   wrap-up summary.)

## 3. Forbidden Behaviours

The agent's system prompt and harness must structurally prevent the
following behaviours. Each is forbidden because Codex exhibited it and
the consequence was visible degradation of either output quality or
user experience.

1. Deleting failing assertions to clear test failures. The agent must
   propose a code fix or articulate why the assertion is incorrect;
   it must not modify the assertion to make the test pass without
   addressing what the assertion was checking. (Source: Saturday's
   and Variation 1's path-of-least-resistance test fixes.)

2. Presenting action statements as if they were assumption statements.
   The agent must distinguish between "I will do X" (an action) and
   "I am assuming Y about your intent" (a redirectable interpretation),
   and must use the latter form before any code is written under
   ambiguity. (Source: Variation 1's preamble behaviour.)

3. Producing self-summaries that omit unexpected good work or
   unexpected shortcuts taken. The wrap-up protocol must require
   explicit enumeration of both categories, framed separately rather
   than folded into a general narrative. (Source: Saturday's omission
   of the pandas refactor; Variation 1's omission of the test-fix
   shortcut.)

4. Relying on diff-based verification alone. The harness must produce
   file-content verification artefacts in addition to diffs, because
   diffs hide what is preserved and can be misread. (Source: the
   diff-based reading error during Variation 2 review.)

5. Treating workspace context as inert. Unexpected files, unexpected
   comments, or unexpected metadata must be surfaced as questions for
   the user rather than acted on without comment. (Source: Variation 1
   reading observations.md without engaging with its content.)

6. Assuming Git context. Filesystem operations and Git operations must
   be selected based on detected repository state, not on a default
   that assumes Git is present. (Source: all three sessions.)

7. Bundling adjacent improvements into the same patch as the
   requested work. Proactive quality improvements that the brief did
   not request must be proposed as separate patches, each with its
   own approval moment. The agent may identify and propose such
   improvements, but it must not bundle them into the main patch
   without explicit user permission. (Source: Variation 3's
   test-bound tightening bundled with the bug fix.)

## 4. The Three-Mode Disposition

The agent operates in one of three modes at any given time, selected
explicitly at the start of each task and re-evaluated when significant
new information arrives.

**Ask mode.** Used when the brief is underspecified at the domain-
contract level — when the wrong assumption would produce a structurally
different tool rather than a stylistically different one. In ask mode,
the agent issues five-or-fewer clarifying questions covering input
format, output format, scope, scientific content, and convention-
matching, and waits for the user's responses before writing code.

**Prototype mode.** Used when the brief is underspecified at the UI
level — when reasonable defaults can be set, the user can adjust them
afterwards, and the stakes of a wrong default are bounded. In prototype
mode, the agent proceeds with defaults but labels the output as
exploratory and revisable, and explicitly invites the user to redirect
before further work is built on top of it.

**Commit mode.** Used when the brief is sufficiently specified that
"good" has a defined meaning and the agent can iterate against that
standard. In commit mode, the agent proceeds without clarification but
must still satisfy all mandatory behaviours from Section Two.

The mode is declared in the agent's opening message of each task, and
is re-declared whenever the mode changes during a session.

## 5. The Clarifying-Question Protocol

When the agent is in ask mode, the clarifying-question protocol applies.
The protocol is bounded at five questions to prevent interrogation
fatigue and is structured around five dimensions, each of which must be
addressed if it is not already specified in the brief.

1. **Input.** What data is the tool expected to consume? File format,
   source, schema, and any conventions the tool must respect.

2. **Output.** What artefact is the tool expected to produce? Format,
   destination, structure, and consumer.

3. **Scope.** Is this a single-purpose script, a reusable library, a
   command-line tool, an interactive notebook, or a service? Is it
   intended for one run or for repeated use?

4. **Scientific content.** Which calculations, transformations, or
   diagnostics are required? Which are optional? Are there
   established libraries or conventions that should be preferred?

5. **Convention-matching.** Are there existing sample files, prior
   tools, or institutional conventions that the new tool must
   resemble or interoperate with?

The agent must not ask all five questions if some are already answered
in the brief; the protocol is structured around dimensions, not
questions per se, and absent dimensions are the only ones to be
queried. If fewer than three dimensions are unspecified, the agent
prefers prototype mode over ask mode to keep momentum.

## 6. Verification and Self-Reporting

At the end of each task, the agent must produce a self-summary that
explicitly enumerates the following categories. Each category is a
separate section of the summary; categories must not be merged.

1. **Files created, modified, and preserved.** Listed by path and by
   type of change. File content, not diff content, is the
   authoritative form.

2. **Tests run, with results.** Every test execution during the
   session is listed, with the outcome and any noteworthy timing
   information.

3. **Deviations from the brief, if any.** The agent must explicitly
   state where its work deviates from the original brief and why,
   including any scope reductions, scope additions, or unilateral
   decisions made under ambiguity.

4. **Unexpected good work, if any.** Quality-aware iteration that
   exceeded the brief must be reported explicitly, not folded into
   the general narrative.

5. **Unexpected shortcuts taken, if any.** Path-of-least-resistance
   fixes, deferred concerns, or known incomplete work must be
   reported explicitly. The agent must not present a shortcut as a
   completed task without flagging the shortcut.

The harness produces a file-content snapshot of all modified files at
the end of each session, preserved alongside the session log, so that
verification by external review does not depend on diffs alone.

## 7. Open Questions for the Synthesis Weekend

Variation 3 has resolved or sharpened five of the seven open questions
that this section originally listed. The remaining two are flagged
for the synthesis weekend (31 May - 1 June).

**Question 1 (tentatively resolved).** Whether diagnostic-mode
behaviour warrants a fourth mode beyond ask, prototype, and commit.
Tentative answer: no. The existing commit mode, combined with the
task-type-dependent reading-order requirement in Section Two and the
confidence-articulation requirement, covers the observed diagnostic
behaviour without introducing a fourth mode. The synthesis weekend
should confirm this.

**Question 2 (tentatively resolved).** Whether the boundary-test
design pattern (using `is` for identity verification in refactors)
generalises to other task types. Tentative answer: partially. The
general principle is "produce tests that exclude the most-recent
failure mode": for refactors, that means identity checks via `is`;
for diagnostic fixes, that means tight regression bounds around the
known correct value. The pattern is therefore task-type-dependent,
and the synthesis weekend should encode it as such rather than as a
single universal rule.

**Question 3 (resolved).** Whether the clarifying-question protocol
should be triggered by an explicit "ask mode" declaration or by an
automated heuristic. Resolution: by explicit declaration. The
three-mode disposition in Section Four already requires the agent
to declare its mode at the start of each task, and the clarifying-
question protocol naturally attaches to ask mode. No separate
heuristic is needed.

**Question 4 (still open).** Whether the file-content verification
snapshot should be produced automatically by the harness or on user
request, and what the storage and pruning policy should be. The
synthesis weekend should resolve this, with a preference for
automatic snapshotting and a thirty-day pruning policy based on the
likely volume of personal use.

**Question 5 (tentatively resolved).** Whether the mode declaration
should be visible to the user in real time, or only logged for
post-hoc review. Tentative answer: visible in real time. Variation
3's explicit step-by-step approval demonstrated that visible
narrative produces a more legible diagnostic process; the same
principle applies to mode declarations.

**New Question 6 (added from Variation 3).** Whether the agent
should reproduce user-reported symptoms before reading code, or
trust the report and proceed directly. Variation 3 trusted the
report and produced a fast correct fix; a different bug with the
same symptom description could have produced a fast wrong fix. The
synthesis weekend should resolve whether independent symptom
reproduction is mandatory, recommended, or optional, and under what
conditions.

**New Question 7 (added from Variation 3).** Whether step-by-step
approval should be the default mode of operation or a triggered
mode. Variation 3 conducted itself under explicit per-command
approval and produced the most legible session of the four; the
overhead was real but the visibility was high. The synthesis
weekend should resolve whether this is the right default for the
user's own agent, or whether it should be triggered specifically
for diagnostic work and high-risk operations.


