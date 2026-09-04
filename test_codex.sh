#!/usr/bin/env bash
# test_codex.sh — the check on the Codex harness + paste detection. Stdlib only,
# offline, no keys.
#
# The fixture inherits the SHAPE of a real Codex rollout (session_meta, the
# response_item envelope, apply_patch tool calls, an exec_command git commit, and
# the FOUR ways Codex threads a non-typed block in wearing the user's role) and
# collapses only the CONTENT, so a green here is green on data that occurs.
#
# fixtures-codex/rollout-fixture.jsonl — 16 records:
#
#   INJECTED role:user (must be DROPPED — each one is a context block, not typed)
#     AGENTS.md instructions · <environment_context> · the agent-history
#     continuation · </image> residue
#
#   TYPED (must be KEPT)
#     A  "refactor the http client ... add tests to verify"   -> apply_patch   ARTIFACT
#     B  "add a pre-commit hook and commit it"                -> patch+commit  COMMIT
#     C  <verbatim paste of a long agent message>             -> no tool       NONE  (PASTE)
#     D  "run the tests"                                      -> no tool       NONE  (short, genuine)
#
#   fixtures-codex/history.jsonl — one typed input matching A's opener. history
#   is a WITNESS (a context-free input log), not an episode source: it is ingested
#   only to confirm the gate reads the rollout right (history_matched).
#
# Expected (normal)          : harness codex, 4 typed turns, 4 episodes,
#                              tiers commit 1 · artifact 1 · none 2, durable 2,
#                              history 1/1.
# Expected (--verified-human): the PASTE (C) is subtracted -> 3 typed, 3 episodes,
#                              1 flagged; the short genuine turn (D) is NOT flagged.
#
# THE LOAD-BEARING CONTROLS:
#   * the 4 injected role:user records stay OUT (human_turns==4, not 8) — a leak
#     here inflates the human signal loudly instead of silently.
#   * paste is subtracted but the short genuine turn survives — the length floor
#     is what separates an echoed agent paragraph from "run the tests".
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
J=$(python3 transcripto.py coach --root fixtures-codex --json)
V=$(python3 transcripto.py coach --root fixtures-codex --verified-human --json)

check () {  # check <name> <json blob> <python expr over r> <expected>
  got=$(printf '%s' "$2" | python3 -c "import json,sys;r=json.load(sys.stdin);print($3)")
  if [ "$got" = "$4" ]; then printf '  ok    %-46s %s\n' "$1" "$got"; PASS=$((PASS+1))
  else printf '  FAIL  %-46s got %s, want %s\n' "$1" "$got" "$4"; FAIL=$((FAIL+1)); fi
}

echo "trace coach --harness codex — assertions on a real-shaped Codex fixture"
echo
echo "the connector + the gate (4 injected role:user disguises must drop)"
check "auto-detects the codex harness"        "$J" "r['harness']"                  codex
check "only the 4 turns you actually typed"   "$J" "r['human_turns']"              4
check "no injected AGENTS/env/continuation"   "$J" "sum('AGENTS' in e or 'environment_context' in e or 'Codex agent history' in e for e in [(r['best_prompt'] or {}).get('opener',''),(r['worst_prompt'] or {}).get('opener','')])" 0

echo
echo "episodes + survival tiers (apply_patch -> artifact, git commit -> commit)"
check "one episode per typed intent"          "$J" "r['episodes']"                 4
check "apply_patch witnessed as artifact"     "$J" "r['tiers']['artifact']"        1
check "git commit witnessed as commit"        "$J" "r['tiers']['commit']"          1
check "nothing durable for the rest"          "$J" "r['tiers']['none']"            2
check "survived = commit + artifact only"     "$J" "r['durable']"                  2

echo
echo "history.jsonl is ingested as the gate control, not an episode source"
check "history line read"                     "$J" "r['history_lines']"            1
check "history text matches a typed turn"     "$J" "r['history_matched']"          1

echo
echo "paste detection (--verified-human subtracts echoed agent output)"
check "one typed turn flagged likely-pasted"  "$V" "r['pastes_flagged']"           1
check "the paste is subtracted from humans"   "$V" "r['human_turns']"              3
check "and dropped from the episodes"         "$V" "r['episodes']"                 3
check "the short genuine turn is NOT flagged" "$V" "(r['worst_prompt'] or {}).get('opener','')" "run the tests"

echo
if [ "$FAIL" -eq 0 ]; then echo "$PASS/$((PASS+FAIL)) green."; else echo "$PASS/$((PASS+FAIL)) — $FAIL RED."; exit 1; fi
