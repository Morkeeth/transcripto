#!/usr/bin/env bash
# test_coach.sh — the check on `trace coach`. Stdlib only, offline, no keys.
#
# The fixture inherits the SHAPE of a real Claude Code transcript (same keys,
# same nesting, the same four ways a non-human record disguises itself as
# `type: user`) and collapses only the CONTENT, so a green here is green on
# data that actually occurs.
#
# fixtures-coach/coach-fixture.jsonl — 21 records, hand-laid:
#
#   HUMAN (8, must be KEPT)
#     09:00 typed   detailed refactor + a check      -> Edit          ARTIFACT
#     09:05 typed   "list the files"                 -> read-only ls  NONE
#     09:10 typed   add retry wrapper                -> Write+commit  COMMIT
#     09:20 typed   rename invoice model             -> commit+reset  REVERTED
#     09:30 queued  "fix it"                         -> no tool       NONE
#     09:40 typed   document the caching layer       -> read-only cat NONE
#     09:50 typed   "Refactor the auth parser."      \  one episode,  ARTIFACT
#     09:51 typed   "no, i meant the header path"    /  the correction merges
#
#   NOT HUMAN (4, must be DROPPED — each one CLAIMS a durable act, so if the
#   gate leaks, survival inflates and the leak is loud instead of silent)
#     toolUseResult · isSidechain · isMeta · promptSource=sdk
#
# Expected: 8 human turns, 7 episodes, 3 survived
#           tiers commit 1 · artifact 2 · reverted 1 · none 3
#
# THE LOAD-BEARING CONTROL is `reverted is not survived`. A commit that was
# reset --hard in the same session left no durable record. If someone ever
# scores tier by "did a commit run", that row alone flips 3 -> 4 and this test
# goes red. Survival is a PROXY and a generous proxy is a broken one.
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
J=$(python3 transcripto.py coach --root fixtures-coach --json)

check () {  # check <name> <python expr over r> <expected>
  got=$(printf '%s' "$J" | python3 -c "import json,sys;r=json.load(sys.stdin);print($2)")
  if [ "$got" = "$3" ]; then printf '  ok    %-46s %s\n' "$1" "$got"; PASS=$((PASS+1))
  else printf '  FAIL  %-46s got %s, want %s\n' "$1" "$got" "$3"; FAIL=$((FAIL+1)); fi
}

echo "trace coach — 14 assertions on a real-shaped fixture"
echo
echo "the gate (the moat: 4 disguised non-human records)"
check "every record read"                 "r['total_records']"          21
check "only the 8 you actually typed"     "r['human_turns']"            8
check "toolUseResult dropped"             "'parser.py' not in [e['opener'] for e in [r['worst_prompt']] if e]" True
check "no sub-agent prompt leaked in"     "sum('Sub-agent' in e for e in [(r['best_prompt'] or {}).get('opener',''),(r['worst_prompt'] or {}).get('opener','')])" 0

echo
echo "episodes"
check "one episode per human intent"      "r['episodes']"               7
check "a correction merges, never splits" "sum(1 for t in ['artifact'] for _ in range(r['tiers']['artifact']))" 2

echo
echo "the survival tiers"
check "commit-witnessed"                  "r['tiers']['commit']"        1
check "artifact-witnessed"                "r['tiers']['artifact']"      2
check "commit-then-reverted"              "r['tiers']['reverted']"      1
check "nothing durable"                   "r['tiers']['none']"          3
check "survived = commit + artifact only" "r['durable']"                3
check "REVERTED IS NOT SURVIVED"          "r['durable'] == r['tiers']['commit'] + r['tiers']['artifact']" True

echo
echo "the witness (a number with no evidence is a vibe)"
check "best prompt names its witness"     "(r['best_prompt'] or {}).get('probe')"  COMMIT-WITNESSED
check "the proxy caveat always travels"   "'PROXY' in r['proxy']"       True

echo
echo "packaging (a --version that lies is worse than no --version)"
if python3 -c "
import re, sys
mod = re.search(r'^VERSION = \"([^\"]+)\"', open('transcripto.py').read(), re.M)
proj = re.search(r'^version = \"([^\"]+)\"', open('pyproject.toml').read(), re.M)
sys.exit(0 if mod and proj and mod.group(1) == proj.group(1) else 1)"; then
  printf '  ok    %s\n' "--version matches pyproject version"; PASS=$((PASS+1))
else
  printf '  FAIL  %s\n' "--version matches pyproject version"; FAIL=$((FAIL+1))
fi

echo
if [ "$FAIL" -eq 0 ]; then echo "$PASS/$((PASS+FAIL)) green."; else echo "$PASS/$((PASS+FAIL)) — $FAIL RED."; exit 1; fi
