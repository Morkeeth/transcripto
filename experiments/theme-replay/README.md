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
PYTHONPATH=. python3 -m theme_replay review .trial/runs --frozen .trial/frozen \
  --decide finish-line-moves KEEP "The correction is on the page."
```

Live generative Gateway is opt-in and fail-closed. It posts to `/v1/chat/completions` with `providerOptions.gateway.zeroDataRetention` and `disallowPromptTraining`. `--zdr` and `--no-training` are required. Wall-clock `latency_ms` is recorded on the receipt.

```sh
PYTHONPATH=. python3 -m theme_replay run .trial/frozen \
  --models anthropic/claude-sonnet-5,openai/gpt-5.6-sol,google/gemini-3.7-flash \
  --zdr --no-training \
  --out .trial/runs-live
```

That path cannot serve Jev. Jev (`typesafe-ai/jev`) is a separate evaluation trial on `POST /v1/evaluate`. This runner refuses Jev model ids so the two trials stay distinct.

Human decisions are KEEP, REVISE, or REJECT plus one sentence. `CHANGES MY VIEW` is accepted as REVISE.

Stage 1 (redacted real episodes) is not in this tree.
