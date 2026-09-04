#!/usr/bin/env bash
# Codex call-only transcripts: authorship and paste gates still work; results stay unknown.
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
check "apply_patch witnessed as artifact"     "$J" "r['tiers']['artifact']"        0
check "git commit witnessed as commit"        "$J" "r['tiers']['commit']"          0
check "nothing durable for the rest"          "$J" "r['tiers']['none']"            2
check "survived = commit + artifact only"     "$J" "r['durable']"                  0

echo
echo "history.jsonl is ingested as the gate control, not an episode source"
check "history line read"                     "$J" "r['history_lines']"            1
check "history text matches a typed turn"     "$J" "r['history_matched']"          1

echo
echo "paste detection (--verified-human subtracts echoed agent output)"
check "one typed turn flagged likely-pasted"  "$V" "r['pastes_flagged']"           1
check "the paste is subtracted from humans"   "$V" "r['human_turns']"              3
check "and dropped from the episodes"         "$V" "r['episodes']"                 3
check "missing results stay unknown" "$V" "r['tiers']['unknown']" 2

echo
if [ "$FAIL" -eq 0 ]; then echo "$PASS/$((PASS+FAIL)) green."; else echo "$PASS/$((PASS+FAIL)) — $FAIL RED."; exit 1; fi
