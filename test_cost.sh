#!/usr/bin/env bash
# test_cost.sh — the check on `trace cost`. Stdlib only, offline, no keys.
#
# The fixture inherits the SHAPE of a real Claude Code transcript (same keys,
# same nesting, same usage object) and collapses only the CONTENT, so a green
# here is green on data that actually occurs.
#
# Hand-computed expected total, at Anthropic list price:
#   msg_A  opus-5      1k in + 1k out            $0.030   <- written to 3 lines
#   msg_B  opus-5      100k 1h-write + 100k read $1.050
#   msg_C  sonnet-5    1M in, intro window       $2.000
#   msg_D  unknown model                         UNPRICED
#   msg_E  haiku-4-5-20251001 (dated) 1M in      $1.000
#   msg_F  opus-4-8    1M out, SUB-AGENT run     $25.000
#                                                -------
#                                                $29.080  / 2 decisions = $14.54
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
J=$(python3 transcripto.py cost --days 0 --root fixtures --json)

check () {  # check <name> <jq-ish python expr> <expected>
  got=$(printf '%s' "$J" | python3 -c "import json,sys;r=json.load(sys.stdin);print($2)")
  if [ "$got" = "$3" ]; then printf '  ok    %-46s %s\n' "$1" "$got"; PASS=$((PASS+1))
  else printf '  FAIL  %-46s got %s, want %s\n' "$1" "$got" "$3"; FAIL=$((FAIL+1)); fi
}

echo "trace cost — 12 assertions on a real-shaped fixture"
echo
echo "the number"
check "total API-equivalent spend"        "round(r['usd'],3)"            "29.08"
check "cost per human decision"           "round(r['per_decision'],2)"   "14.54"

echo "the denominator: is_human_turn, not type:user"
check "decisions counted"                 "r['decisions']"               "2"
check "raw type:user records, for contrast" "r['raw_user_turns']"          "6"
check "  gate factor is printed, not claimed" "round(r['gate_factor'],1)"  "3.0"
# sdk + isMeta + toolUseResult + isSidechain user rows are all type:user and all
# must be invisible here. 6 user rows in the fixture, 2 of them are decisions.

echo "the numerator: dedupe, sub-agents, cache tiers, unknown models"
# msg_A occupies 3 transcript lines with an identical usage object. Summing lines
# gives 9 messages and \$29.14. This assertion is the whole reason the number is right.
check "one API message counted once"      "r['agent_messages']"          "6"
check "  (not once per content block)"    "int(r['agent_messages']!=8)"  "1"
check "sub-agent tokens are your spend"   "round(r['by_model']['claude-opus-4-8']['usd'],2)" "25.0"
check "1h cache write billed at 2x input" "round(r['by_model']['claude-opus-5']['usd'],3)"   "1.08"
check "dated model id normalises"         "round(r['by_model']['claude-haiku-4-5']['usd'],2)" "1.0"
check "unknown model = UNPRICED"          "int(r['by_model']['claude-notarealmodel-9']['priced'])" "0"
check "  ...and never a silent \$0"        "r['unpriced_tokens']"         "2000"

echo
if [ "$FAIL" -eq 0 ]; then echo "$PASS/$((PASS+FAIL)) green."; exit 0
else echo "$FAIL of $((PASS+FAIL)) FAILED."; exit 1; fi
