#!/usr/bin/env bash
# test_label_bands.sh — SURVIVES MOST and SURVIVES LEAST must never name the same habit.
#
# Why this file exists. `fixtures-small-n` pins the refusal band (9 EPISODES, under
# MIN_EPISODES_TO_RANK, so no ranked table prints at all). Nothing pinned the band
# where the corpus IS rankable but the habit LABELS are few — and that is the band
# every first-time user starts in. There, `rankable[:5]` and `rankable[-5:]`
# overlapped, so coach printed the same habit, at the same percentage, with the same
# denominator, under both "do more of these" and "these tend to loop".
#
# Measured 2026-08-31 against the published 0.1.1 wheel:
#   fixtures-few-labels    (3 habits) -> 0.1.1 reprinted ALL THREE, all at 65% (22/34)
#   fixtures-narrow-labels (6 habits) -> 0.1.1 reprinted 4 of the 5 top rows
#   fixtures-wide-labels  (10 habits) -> 0.1.1 output is byte-identical to the fix
# The last line is the one that keeps the fix honest: it must not move a big corpus.
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
check () {
  if eval "$2"; then printf '  ok    %s\n' "$1"; PASS=$((PASS+1))
  else printf '  FAIL  %s\n' "$1"; FAIL=$((FAIL+1)); fi
}
# disjoint <root> — TOP and BOTTOM must share no habit name.
disjoint () {
  python3 transcripto.py coach --root "$1" --json | python3 -c "
import json,sys
r = json.load(sys.stdin)
t = {p['pattern'] for p in r['top_patterns']}
b = {p['pattern'] for p in r['bottom_patterns']}
sys.exit(0 if not (t & b) else 1)"
}
# no_dup_rows <root> — no PRINTED percentage row may appear twice in the output.
no_dup_rows () {
  test "$(python3 transcripto.py coach --root "$1" 2>&1 \
          | grep -oE '^ +[0-9]+% +\([0-9]+/[0-9]+\) .*$' | sort | uniq -d | wc -l)" -eq 0
}
labels () {
  python3 transcripto.py coach --root "$1" --json | python3 -c "
import json,sys; r=json.load(sys.stdin)
print(len(r['top_patterns']) + len(r['bottom_patterns']))"
}

echo "label bands — the same habit must never be both the advice and the warning"
echo

echo " few (3 rankable habits, 34 episodes)"
check "corpus is rankable, so the table does print" \
  "python3 transcripto.py coach --root fixtures-few-labels 2>&1 | grep -q 'SURVIVES MOST'"
check "TOP and BOTTOM name no habit in common" "disjoint fixtures-few-labels"
check "no printed row appears twice" "no_dup_rows fixtures-few-labels"
check "with nothing left over, SURVIVES LEAST does not print a bare header" \
  "! python3 transcripto.py coach --root fixtures-few-labels 2>&1 | grep -q 'SURVIVES LEAST'"
check "it says why instead of printing nothing" \
  "python3 transcripto.py coach --root fixtures-few-labels 2>&1 | grep -q 'too few to split'"

echo " narrow (6 rankable habits, 36 episodes) — the band that used to overlap"
check "the fixture really is in the 6-9 band" "test \"\$(labels fixtures-narrow-labels)\" -ge 6 -a \"\$(labels fixtures-narrow-labels)\" -le 9"
check "TOP and BOTTOM name no habit in common" "disjoint fixtures-narrow-labels"
check "no printed row appears twice" "no_dup_rows fixtures-narrow-labels"
check "SURVIVES LEAST still prints, with what is genuinely left" \
  "python3 transcripto.py coach --root fixtures-narrow-labels 2>&1 | grep -q 'SURVIVES LEAST'"

echo " wide (10 rankable habits, 100 episodes) — must be untouched by the fix"
check "both tables are full at 5" \
  "test \"\$(labels fixtures-wide-labels)\" -eq 10"
check "TOP and BOTTOM name no habit in common" "disjoint fixtures-wide-labels"
check "no printed row appears twice" "no_dup_rows fixtures-wide-labels"
check "every BOTTOM habit really does rank below every TOP habit" \
  "python3 transcripto.py coach --root fixtures-wide-labels --json | python3 -c \"
import json,sys
r = json.load(sys.stdin)
t = [p['survival_rate'] for p in r['top_patterns']]
b = [p['survival_rate'] for p in r['bottom_patterns']]
sys.exit(0 if not b or min(t) >= max(b) else 1)\""

echo
if [ "$FAIL" -eq 0 ]; then echo "$PASS/$((PASS+FAIL)) green."; else echo "$PASS/$((PASS+FAIL)) — $FAIL RED."; exit 1; fi
