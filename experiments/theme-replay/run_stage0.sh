#!/usr/bin/env bash
# One command for the Stage 0 memo comparison.
#
#   ./run_stage0.sh            live if OPENROUTER_API_KEY is set, else offline mechanics only
#   ./run_stage0.sh --offline  offline mechanics only, no network
#   ./run_stage0.sh --rescore  no network: re-verify and re-score the committed results
#
# Live spend is capped by MAX_COST (USD, default 10) through one shared ledger.
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH=.

MODELS="${MODELS:-anthropic/claude-sonnet-5,openai/gpt-5.6-sol,google/gemini-3.7-flash}"
WRITER="${WRITER:-moonshotai/kimi-k3}"
MAX_COST="${MAX_COST:-10}"
SEED="${SEED:-20260922}"
STAMP="${STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
TRIAL=".trial/stage0-$STAMP"
RESULTS="results/stage0-2026-09-22"
EXPECTED_SHA="ad4cd9260a25d6561cd5421e4eb07b189284df22626a59bac4c04739ec8b5392"

mode="live"
[ "${1:-}" = "--offline" ] && mode="offline"
[ "${1:-}" = "--rescore" ] && mode="rescore"
[ "$mode" = "live" ] && [ -z "${OPENROUTER_API_KEY:-}" ] && mode="offline"
echo "MODE $mode"

if [ "$mode" = "rescore" ]; then
  python3 -m theme_replay rescore "$RESULTS"
  exit $?
fi

python3 -m theme_replay freeze fixtures/stage0-episodes.jsonl \
  --question fixtures/question.txt --prompt "${PROMPT:-fixtures/analysis-prompt-v2.txt}" --out "$TRIAL/frozen" >/dev/null
sha=$(python3 -c "import json;print(json.load(open('$TRIAL/frozen/dataset-manifest.json'))['files']['episodes.jsonl'])")
if [ "$sha" != "$EXPECTED_SHA" ]; then echo "FROZEN CORPUS CHANGED: $sha"; exit 3; fi
echo "CORPUS sha256 $sha (unchanged)"

if [ "$mode" = "offline" ]; then
  python3 -m theme_replay run "$TRIAL/frozen" --offline fixtures/offline-arms --out "$TRIAL/runs" --seed "$SEED" >/dev/null
  python3 -m theme_replay verify "$TRIAL/frozen" "$TRIAL/runs" | head -3
  python3 -m theme_replay compare "$TRIAL/frozen" "$TRIAL/runs" >/dev/null
  echo "Offline mechanics only. The memo comparison needs live readings."
  exit 0
fi

python3 -m theme_replay run "$TRIAL/frozen" --transport openrouter --models "$MODELS" \
  --repeat 3 --seed "$SEED" --max-cost "$MAX_COST" --ledger "$TRIAL/spend.json" --out "$TRIAL/runs" >/dev/null
set +e
python3 -m theme_replay verify "$TRIAL/frozen" "$TRIAL/runs" >/dev/null
echo "VERIFY exit $? (2 means named citation failures; see verify.json)"
set -e
python3 -m theme_replay compare "$TRIAL/frozen" "$TRIAL/runs" >/dev/null
python3 -m theme_replay memo "$TRIAL/frozen" "$TRIAL/runs" --out "$TRIAL/memos" --models "$MODELS" \
  --writer "$WRITER" --seed "$SEED" --max-cost "$MAX_COST" --ledger "$TRIAL/spend.json"
python3 -m theme_replay publish "$TRIAL" "$RESULTS"
echo "RESULTS $RESULTS  (raw bodies and blind keys stay in $TRIAL, mode 0600)"
