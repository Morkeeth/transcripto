# Helicon method-conformance checklist · Stage 0

Helicon may check process. It must not score thematic truth.

- [x] Dataset, question, prompt, and protocol have hashes in `dataset-manifest.json` after freeze.
- [x] Stage 0 episodes are synthetic and contain no `/Users/`, home, or harness-store paths.
- [x] Every quote and line must resolve to the frozen corpus or the arm is named as a failure.
- [x] `failed` and `unknown` statuses cannot be upgraded to succeeded.
- [x] Themes must include a disconfirming episode.
- [x] Human decisions are KEEP / REVISE / REJECT plus one sentence.
- [x] Gateway is opt-in, fail-closed, and not on Transcripto's default path.
- [x] Raw live receipts are mode 0600 under `.trial/` and are gitignored.
- [ ] Human baseline before live model exposure is still owed for Stage 1.
- [ ] Stage 1 redacted export is not started.

Helicon must not write to `~/.trace/trace.db`.
