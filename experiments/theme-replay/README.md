# Theme Replay · Stage 0

Opt-in experiment. It is not on Transcripto's default path and it does not send private transcripts.

Frozen question: **What makes an agent-work episode require correction?**

The corpus is 12 synthetic episodes (4 Claude, 4 Codex, 4 Cursor). Each harness has one succeeded change, one failed change, one unknown result, and one changed-decision episode.

```sh
cd experiments/theme-replay
PYTHONPATH=. python3 -m theme_replay freeze fixtures/stage0-episodes.jsonl \
  --question fixtures/question.txt \
  --prompt fixtures/analysis-prompt.txt \
  --out .trial/frozen

PYTHONPATH=. python3 -m theme_replay run .trial/frozen \
  --offline fixtures/offline-arms \
  --out .trial/runs

PYTHONPATH=. python3 -m theme_replay verify .trial/frozen .trial/runs
PYTHONPATH=. python3 -m theme_replay compare .trial/frozen .trial/runs
PYTHONPATH=. python3 -m theme_replay review .trial/runs --frozen .trial/frozen \
  --decide finish-line-moves KEEP "The correction is on the page."
```

Receipts are blind. `run` shuffles arms with a recorded `--seed` and names them `arm-N.json`. The arm-to-model key is `blind.json` (mode 0600). `review` and `compare` never read model ids from receipts.

`compare` is the arm M view. It lists shared readings, unique readings, contested episodes (support in one arm, counterexample in another), uncited episodes and repeat drift. Two themes count as one reading when their supporting episodes overlap by at least half. It gives no single number. Overlap is not validity.

`verify` checks every arm, even one without codes. It names: quotes or lines that do not resolve, codes with no evidence, episode ids that do not exist (in codes, counterevidence, supporting and disconfirming lists), themes that name a code nobody defined, themes with no disconfirming episode, and a `claimed_status` that differs from the status on the cited line.

Live generative Gateway is opt-in and fail-closed. It posts to `/v1/chat/completions` with `providerOptions.gateway.zeroDataRetention` and `disallowPromptTraining`. `--zdr` and `--no-training` are required. Wall-clock `latency_ms` is recorded on the receipt.

```sh
PYTHONPATH=. python3 -m theme_replay run .trial/frozen \
  --models anthropic/claude-sonnet-5,openai/gpt-5.6-sol,google/gemini-3.7-flash \
  --zdr --no-training --repeat 2 \
  --out .trial/runs-live
```

A live run checks for a key before any network request. It then freezes `model-manifest.json` from the public `/v1/models` catalogue and refuses any model that is missing or publishes no ZDR or no-training route. `--repeat 2` issues separate requests, never a fallback chain. Each receipt keeps the whole `providerMetadata.gateway` blob and says `zdr_confirmation: unverified`, because no live response has shown which field proves ZDR routing.

That path cannot serve Jev. Jev (`typesafe-ai/jev`) is a separate evaluation trial on `POST /v1/evaluate`. This runner refuses Jev model ids so the two trials stay distinct.

Human decisions are KEEP, REVISE, or REJECT plus one sentence. `CHANGES MY VIEW` is accepted as REVISE.

Stage 1 (redacted real episodes) is not in this tree.
