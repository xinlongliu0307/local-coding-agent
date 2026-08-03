
## Reissue retry: first live firing (ninth emission failure)

On the freshpool task the 32B emitted a tool call as text twice in
succession. The detector caught both, the loop injected the correction
message each time, and the bounded counter terminated cleanly after two
attempts rather than looping. The recovery mechanism works as designed.

The model did not comply even when told explicitly, so the retry converts
a silent failure into a diagnosed one but does not fix the underlying
model behaviour. Plan for the hand fallback on write-heavy single-shot
tasks regardless.

## Empty-old_string file creation (7B), and a false self-summary

On the nino34 parser task the 7B twice used edit_file with an empty
old_string to create a file that did not exist. The Phase Twenty guard
refused both, correctly. The model then reported the file as written
without having written it, which is the self-summary fidelity failure
documented in the original Codex trials, now reproduced locally.

The reissue retry did not fire, correctly: these were well-formed tool
calls, not text emissions. The detector discriminates as intended.

Design implication: the system prompt should state that write_file, not
edit_file, is the tool for creating a new file. The guard prevents damage
but the model wastes iterations rediscovering it.
