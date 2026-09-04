#!/usr/bin/env bash
# test_small_n.sh — STEP 0 gate: at n=9, coach must refuse the ranked table.
# Synthetic 9-transcript corpus (BUILD-PLAN-2026-08-27 § STEP 0 verification).
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0

check () {
  if eval "$2"; then printf '  ok    %s\n' "$1"; PASS=$((PASS+1))
  else printf '  FAIL  %s\n' "$1"; FAIL=$((FAIL+1)); fi
}

OUT=$(python3 transcripto.py coach --root fixtures-small-n 2>&1)
J=$(python3 transcripto.py coach --root fixtures-small-n --json)

echo "STEP 0 — small-n gate (9 synthetic transcripts)"
echo
check "9 episodes extracted" \
  "printf '%s' '$J' | python3 -c \"import json,sys; r=json.load(sys.stdin); exit(0 if r['episodes']==9 else 1)\""
check "rankable_corpus is false" \
  "printf '%s' '$J' | python3 -c \"import json,sys; r=json.load(sys.stdin); exit(0 if not r['rankable_corpus'] else 1)\""
check "honest refusal message printed" \
  "echo '$OUT' | grep -q 'Small history:'"
check "no SURVIVES MOST table" \
  "! echo '$OUT' | grep -q 'SURVIVES MOST'"
check "no SURVIVES LEAST table" \
  "! echo '$OUT' | grep -q 'SURVIVES LEAST'"
check "no pattern denominator (x/y) below MIN_PATTERN_N" \
  "! echo '$OUT' | grep -Eq '\\([0-9]+/[0-9]+\\)'"
check "raw survival line still shown" \
  "echo '$OUT' | grep -q 'episodes: 9 observed'"

echo
if [ "$FAIL" -eq 0 ]; then echo "$PASS/$((PASS+FAIL)) green."; else echo "$PASS/$((PASS+FAIL)) — $FAIL RED."; exit 1; fi
