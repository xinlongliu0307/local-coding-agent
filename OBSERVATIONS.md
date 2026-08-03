
## Reissue retry: first live firing (ninth emission failure)

On the freshpool task the 32B emitted a tool call as text twice in
succession. The detector caught both, the loop injected the correction
message each time, and the bounded counter terminated cleanly after two
attempts rather than looping. The recovery mechanism works as designed.

The model did not comply even when told explicitly, so the retry converts
a silent failure into a diagnosed one but does not fix the underlying
model behaviour. Plan for the hand fallback on write-heavy single-shot
tasks regardless.
