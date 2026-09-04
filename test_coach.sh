#!/usr/bin/env bash
# Legacy call-only fixtures must not be promoted to successful execution.
# Result-bearing success/failure contracts live in tests/test_replay.py.
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
check "one episode per human intent"      "r['episodes']"               8
check "missing results have unknown outcomes" "r['tiers']['unknown']" 4

echo
echo "the survival tiers"
check "commit-witnessed"                  "r['tiers']['commit']"        0
check "artifact-witnessed"                "r['tiers']['artifact']"      0
check "commit-then-reverted"              "r['tiers']['reverted']"      0
check "nothing durable"                   "r['tiers']['none']"          4
check "survived = commit + artifact only" "r['durable']"                0
check "REVERTED IS NOT SURVIVED"          "r['durable'] == r['tiers']['commit'] + r['tiers']['artifact']" True

echo
echo "the witness (a number with no evidence is a vibe)"
check "no invented best prompt" "r['best_prompt']" None
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
