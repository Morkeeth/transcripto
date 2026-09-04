#!/usr/bin/env bash
# test_cursor_partial.sh — a PARTIAL tool call must not abort the run.
#
# Cursor persists an in-flight tool call with its arguments still a raw JSON
# string prefix ({"contents": "). Exactly one such record in a 13,073-record
# corpus was enough to abort `coach --harness cursor` with
#   AttributeError: 'str' object has no attribute 'get'
# so the command the README sells as one of three harnesses never ran at all.
#
# The load-bearing assertion is EXIT 0 WITH A STRING INPUT PRESENT. Revert the
# _tool_input guard and this suite goes red on the first check.
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0

check () {
  if eval "$2"; then printf '  ok    %s\n' "$1"; PASS=$((PASS+1))
  else printf '  FAIL  %s\n' "$1"; FAIL=$((FAIL+1)); fi
}

OUT=$(python3 transcripto.py coach --root fixtures-cursor --harness cursor 2>&1); RC=$?
J=$(python3 transcripto.py coach --root fixtures-cursor --harness cursor --json 2>/dev/null)

jq_ () { printf '%s' "$J" | python3 -c "import json,sys; r=json.load(sys.stdin); exit(0 if ($1) else 1)"; }

echo "cursor — a partial tool call is not a crash"
echo

check "the fixture really carries a string tool input" \
  "grep -q '\"input\": \"{\\\\\"contents' fixtures-cursor/projects/-tmp-demo/agent-transcripts/*/*.jsonl"
check "PARTIAL TOOL CALL IS NOT A CRASH — exit 0" \
  "[ $RC -eq 0 ]"
check "no traceback" \
  "! echo '$OUT' | grep -q 'Traceback'"
check "3 episodes extracted (nothing dropped)" \
  "jq_ \"r['episodes']==3\""
check "partial writes stay unknown" \
  "jq_ \"r['tiers']['unknown']==2\""
check "the partial Bash claims no commit" \
  "jq_ \"r['tiers']['commit']==0\""
check "no successful change is invented" \
  "jq_ \"r['durable']==0\" "

echo
if [ "$FAIL" -eq 0 ]; then echo "$PASS/$((PASS+FAIL)) green."; else echo "$PASS/$((PASS+FAIL)) — $FAIL RED."; exit 1; fi
