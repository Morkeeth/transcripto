# Theme Replay · Stage 0

Opt-in experiment. It is not on Transcripto's default path and it does not send private transcripts.

Frozen question: **What makes an agent-work episode require correction?**

The live run uses `fixtures/analysis-prompt-v2.txt` (adds the PRD schema and the `L<n>` line view). The commands below show v1, which the offline arms and tests use.

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

Receipts are blind. `run` shuffles arms with a recorded `--seed` and names them `arm-N.json`. The arm-to-model key is `blind.json` (mode 0600). Receipts carry no model id. `review` never opens `blind.json`. `compare` reads it only to group repeats, and emits `G1`, `G2` labels.

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

## Memo comparison (added 2026-09-22)

Question: does model disagreement improve an evidence-linked analytic memo?

```sh
cd experiments/theme-replay
./run_stage0.sh            # live if OPENROUTER_API_KEY is set, else offline mechanics
./run_stage0.sh --rescore  # no network: re-verify and re-score results/stage0-2026-09-22
```

- Transport is OpenRouter, not Vercel AI Gateway. No Gateway key exists on this machine. Receipts say `transport: openrouter`. The request asks for `zdr: true` and `data_collection: deny`; whether a provider honoured that is `unverified`. Stage 1 real data must not use this path until it is proven.
- Three analysis families, three separate requests each (`--repeat 3`), one shared spend ledger with a USD ceiling (`MAX_COST`, default 10).
- A fixed writer model (`moonshotai/kimi-k3`, outside the three families) stands in for the analyst. It writes memos under four conditions: B (no readings), S (one reading), R (three repeats of one family plus the divergence view), M (three families plus the divergence view). M versus R is the primary contrast.
- Scoring and the decision rule are in `fixtures/memo-protocol.json`, committed before any live output.
- `results/stage0-2026-09-22/memos/human-packet.md` is blind. Rate it before you open `memo-report.json`. The model-to-arm key and the packet key stay in `.trial/` (0600, gitignored).
- The writer is a proxy. It is not the human H or H+M arm in the PRD.
