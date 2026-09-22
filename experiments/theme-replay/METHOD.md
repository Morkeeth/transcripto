# Helicon method-conformance checklist · Stage 0

Helicon may check process. It must not score thematic truth.

- [x] Dataset, question, prompt, and protocol have hashes in `dataset-manifest.json` after freeze.
- [x] Stage 0 episodes are synthetic and contain no `/Users/`, home, or harness-store paths.
- [x] Every quote and line must resolve to the frozen corpus or the arm is named as a failure.
- [x] `failed` and `unknown` statuses cannot be upgraded to succeeded.
- [x] Themes must include a disconfirming episode.
- [x] Human decisions are KEEP / REVISE / REJECT plus one sentence.
- [x] Gateway is opt-in, fail-closed, and not on Transcripto's default path.
- [x] Live generative requests put `zeroDataRetention` and `disallowPromptTraining` under `providerOptions.gateway`, not at the top level.
- [x] Live generative receipts record wall-clock `latency_ms`.
- [x] `/v1/chat/completions` is generative only. Jev stays on `/v1/evaluate` and is refused here.
- [x] Raw live receipts are mode 0600 under `.trial/` and are gitignored.
- [x] Every arm is validated, including arms with no `codes` key. Verify recomputes and does not trust receipt errors.
- [x] Claimed statuses must match the status on the cited line, not the episode as a whole.
- [x] Episode ids in codes, counterevidence, supporting and disconfirming lists must exist.
- [x] Arms are blind: seeded shuffle, `arm-N` names, key in 0600 `blind.json`.
- [x] `compare` reports overlap, unique readings, contested episodes, uncited episodes and repeat drift. No single number.
- [x] Live runs freeze a model manifest from the public catalogue before any paid call, and check for a key before any network request.
- [x] Live run 2026-09-22 through OpenRouter, not Gateway: 9 arms, 0 unresolved citations, 12 proxy memos. `zdr_confirmation: unverified`. See `results/stage0-2026-09-22/`.
- [ ] No live Gateway run yet. No key is configured. Which response field proves ZDR routing is unverified.
- [ ] Human KEEP / REVISE / REJECT decisions by Oscar are still owed. Decisions on record so far came from agents.
- [ ] Human baseline before live model exposure is still owed for Stage 1.
- [ ] Stage 1 redacted export is not started.

Helicon must not write to `~/.trace/trace.db`.
