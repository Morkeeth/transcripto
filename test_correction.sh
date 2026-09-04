#!/usr/bin/env bash
# test_correction.sh — the check on the CORRECTION RATE (coach) and on
# `export-run` (the JSON contract Agent Grinder and ZUP read). Stdlib, offline.
#
# correction rate = typed turns that correct the agent / typed turns. The
# denominator is the same authorship gate every other coach number uses.
#
# fixtures-correction/correction-fixture.jsonl — 16 records, hand-laid, one
# session (fixture-corr-0001, cwd /repo which is NOT a git repo on purpose):
#
#   TYPED (6, the denominator)                                      label
#     09:00 typed   "Refactor the auth parser in src/auth/parser.py…"  NOT (long, no marker)
#     09:05 typed   "no, I meant the header parser in …headers.py"     CORRECTION (marker)
#     09:10 typed   "add a unit test for the expiry branch"            NOT (short, but names
#                                                                          no file the agent
#                                                                          just touched — the
#                                                                          NUDGE control)
#     09:15 typed   "you didn't run the whole suite, run pytest again" CORRECTION (marker)
#     09:20 queued  "document the caching layer in docs/caching.md"    NOT (agent's last turn
#                                                                          named no file)
#     09:25 typed   "docs/caching.md, shorter please"                  CORRECTION (NUDGE: no
#                                                                          marker, 4 words,
#                                                                          the file the agent
#                                                                          just wrote)
#   NOT HUMAN (3, must be DROPPED — each one carries a marker, so a leaking gate
#   moves the rate instead of hiding inside it)
#     toolUseResult "no, wrong file"  ·  isMeta "stop"  ·  isSidechain "docs/caching.md again"
#
# Expected: 6 typed, 3 corrections, rate 0.5. A leaking gate reads 9 typed / 5 = 0.556.
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
SCRATCH="${TMPDIR:-/tmp}/transcripto-test-correction.$$"

check () {  # check <name> <python expr over r> <expected>
  got=$(printf '%s' "$J" | python3 -c "import json,sys;r=json.load(sys.stdin);print($2)")
  if [ "$got" = "$3" ]; then printf '  ok    %-50s %s\n' "$1" "$got"; PASS=$((PASS+1))
  else printf '  FAIL  %-50s got %s, want %s\n' "$1" "$got" "$3"; FAIL=$((FAIL+1)); fi
}
ok () {  # ok <name> <shell condition>
  if eval "$2"; then printf '  ok    %s\n' "$1"; PASS=$((PASS+1))
  else printf '  FAIL  %s\n' "$1"; FAIL=$((FAIL+1)); fi
}

echo "correction rate + export-run"
echo
echo "the classifier (one pure function; each case is a rule stated in its docstring)"
CLS=$(python3 - <<'PY'
import transcripto as t
cases = [
 ("no",                              "", True,  "a bare 'no' is a correction"),
 ("No, the other one",               "", True,  "marker is case-insensitive"),
 ("That's not what I asked",         "", True,  "that's not"),
 ("revert that",                     "", True,  "revert"),
 ("run it again",                    "", True,  "again"),
 ("Against the grain, add tests",    "", False, "'against' is not 'again' (whole word)"),
 ("undone work is fine",             "", False, "'undone' is not 'undo'"),
 ("stopwatch feature please",        "", False, "'stopwatch' is not 'stop'"),
 ("now add the file",                "", False, "'now' is not 'no '"),
 ("I know nothing about this",       "", False, "'know'/'nothing' are not 'no '"),
 ("x " * 45 + "wrong",               "", False, "a marker past the first 80 chars does not count"),
 ("headers.py please", "[Edit.file_path] /repo/src/http/headers.py", True,  "NUDGE: short turn naming the file the agent just touched"),
 ("headers.py please", "",                                            False, "NUDGE needs a preceding agent turn"),
 ("add a unit test for the expiry branch", "[Edit.file_path] /repo/src/http/headers.py", False, "NUDGE control: short but no shared file"),
 ("please rewrite headers.py so that every helper has a docstring and the tests still pass ok",
  "[Edit.file_path] /repo/src/http/headers.py", False, "NUDGE needs < 12 words"),
 ("use `pytest -q` please", "ran `pytest -q`", True, "NUDGE: a shared backticked command"),
]
bad = [(c[3], t.is_correction(c[0], c[1], version="v0"))
       for c in cases if t.is_correction(c[0], c[1], version="v0") != c[2]]
print(len(cases), len(bad))
for b in bad: print("MISMATCH", b)
PY
)
ok "16 docstring cases, 0 mismatches ($(echo "$CLS" | head -1))" "[ \"$(echo "$CLS" | head -1)\" = '16 0' ]"
ok "is_correction is pure: text + prev_agent + an explicit version, no state" \
  "python3 -c \"import inspect,transcripto as t; s=inspect.signature(t.is_correction); assert list(s.parameters)==['text','prev_agent','version'], list(s.parameters); assert t.is_correction.__doc__; assert t.is_correction('no, wrong',version='v0')==t.is_correction('no, wrong',version='v0')\""

# v1 is a DIFFERENT classifier and gets its own cases, from the failures that
# produced it (docs/CORRECTION-PRECISION-2026-09-03.md). v0's cases above stay
# green because v0 still ships behind TRANSCRIPTO_CORRECTION=v0 — deleting them
# would leave the version Oscar can still select with no coverage at all.
V1=$(python3 - <<'PY'
import transcripto as t
cases = [
 ("no rush, take your time",        False, "bare 'no ' about the world is not a correction (v0 said True)"),
 ("no clue what that is",           False, "'no clue' is not a rejection"),
 ("lets pick this up again",        False, "resuming is not correcting (v0 said True)"),
 ("I will read it once again",      False, "'once again' alone is continuation"),
 ("no, thats wrong",                True,  "'no,' + a complaint"),
 ("no you misunderstood",           True,  "'no' + pronoun"),
 ("try again",                      True,  "retry imperative"),
 ("we mixed up the branches again", True,  "'again' next to a complaint"),
 ("fix it",                         True,  "the shortest correction there is (v0 missed it)"),
 ("i mean the other one",           True,  "'i mean', not just 'i meant' (v0 missed it)"),
 ("dont like the layout",           True,  "rejection of output (v0 missed it)"),
 ("this makes no sense",            True,  "bare verdict"),
 ("wheres the output",              True,  "absence report (v0 missed it)"),
 ("shouldnt this be in hack.md?",   True,  "'shouldnt' (v0 missed it)"),
 ("its not working",                True,  "'not working' (v0 missed it)"),
 ("ok lets go",                     False, "plain assent"),
 ("run the full scan please",       False, "a fresh instruction"),
 ("https://example.com/a.png once again change it", True,
  "the marker survives a leading URL — v0 spent its 80-char window on the URL"),
]
bad = [(c[2], t.is_correction(c[0], version="v1"))
       for c in cases if t.is_correction(c[0], version="v1") != c[1]]
print(len(cases), len(bad))
for b in bad: print("MISMATCH", b)
PY
)
ok "18 v1 cases, 0 mismatches ($(echo "$V1" | head -1))" "[ \"$(echo "$V1" | head -1)\" = '18 0' ]"

echo
echo "the rate on the fixture (coach --json)"
J=$(TRANSCRIPTO_CORRECTION=v0 python3 transcripto.py coach --root fixtures-correction --json)
check "every record read"                     "r['total_records']"   16
check "only the 6 you typed (3 decoys dropped)" "r['human_turns']"   6
check "3 corrections"                         "r['corrections']"     3
check "correction_rate = 3/6"                 "r['correction_rate']" 0.5
OUT=$(TRANSCRIPTO_CORRECTION=v0 python3 transcripto.py coach --root fixtures-correction 2>&1)
ok "coach prints the rate WITH its n"  "echo \"\$OUT\" | grep -q 'correction rate: 50% measured (3 of 6 typed turns)'"
ok "…and names the version and its MEASURED recall, not just 'a floor'" \
  "echo \"\$OUT\" | grep -q 'v0 catches ~1 in 18'"
ok "existing footer line untouched"    "echo \"\$OUT\" | grep -q '6 typed by you'"

echo
echo "the gate is load-bearing: strip the three decoy flags and the rate moves"
mkdir -p "$SCRATCH"
python3 - "$SCRATCH" <<'PY'
import json, sys, os
out = open(os.path.join(sys.argv[1], "leaky.jsonl"), "w")
for line in open("fixtures-correction/correction-fixture.jsonl"):
    d = json.loads(line)
    if d.get("type") == "user":
        d.pop("isMeta", None); d.pop("isSidechain", None); d.pop("toolUseResult", None)
        d["promptSource"] = "typed"
        if isinstance(d["message"].get("content"), list):
            d["message"]["content"] = "no, wrong file - Edit failed"
    out.write(json.dumps(d) + "\n")
PY
J=$(TRANSCRIPTO_CORRECTION=v0 python3 transcripto.py coach --root "$SCRATCH" --json)
check "a leaking gate would count 9 typed"    "r['human_turns']"     9
# 3 decoys each carry a marker (+3); but the leaked sidechain turn now sits between
# the agent's Write and the NUDGE turn, so that one loses its agent context (-1).
check "…and 5 corrections (3 decoys +3, the NUDGE loses its agent turn -1)" "r['corrections']" 5
check "…so the rate would read 0.556, not 0.5" "r['correction_rate']" 0.556

echo
echo "export-run (the JSON contract)"
J=$(TRANSCRIPTO_CORRECTION=v0 python3 transcripto.py export-run correction-fixture --root fixtures-correction)
ok "output is valid JSON" "printf '%s' \"\$J\" | python3 -c 'import json,sys; json.load(sys.stdin)'"
check "schema tag"                    "r['schema']"            transcripto.export-run/1
check "session_id from the records"   "r['session_id']"        fixture-corr-0001
check "project = cwd"                 "r['project']"           /repo
check "harness"                       "r['harness']"           claude
check "started (UTC, Z)"              "r['started']"           2026-08-01T09:00:00Z
check "ended"                         "r['ended']"             2026-08-01T09:25:10Z
check "duration_s"                    "r['duration_s']"        1510
check "typed_turns = coach's denominator" "r['typed_turns']"   6
check "correction_rate matches coach" "r['correction_rate']"   0.5
check "tool_calls"                    "r['tool_calls']"        7
check "files_touched = Edit/Write/Read file_path set, sorted" "r['files_touched']" \
  "['/repo/docs/caching.md', '/repo/src/auth/parser.py', '/repo/src/http/headers.py', '/repo/tests/test_expiry.py']"
check "commits_in_window is null when cwd is not a repo" "r['commits_in_window']" None
ok "'latest' resolves inside --root too" \
  "python3 transcripto.py export-run latest --root fixtures-correction | grep -q fixture-corr-0001"
ok "an unknown session exits 2 and names where it looked" \
  "! python3 transcripto.py export-run no-such-session --root fixtures-correction 2>\"$SCRATCH/err\"; grep -q 'looked in: fixtures-correction' \"$SCRATCH/err\""

echo
echo "commits_in_window reads the reflog, not a subprocess"
mkdir -p "$SCRATCH/repo/.git/logs"
printf '%s\n' \
 "0000000000000000000000000000000000000000 aaaaaaa1111111111111111111111111111111111 A Person <a@b.c> 1787263122 +0200	commit (initial): first" \
 "aaaaaaa1111111111111111111111111111111111 bbbbbbb2222222222222222222222222222222222 A Person <a@b.c> 1787263733 +0200	commit: inside the window" \
 "bbbbbbb2222222222222222222222222222222222 ccccccc3333333333333333333333333333333333 A Person <a@b.c> 1787263800 +0200	rebase (pick): not a commit" \
 "ccccccc3333333333333333333333333333333333 ddddddd4444444444444444444444444444444444 A Person <a@b.c> 1787270000 +0200	commit: after the window" \
 > "$SCRATCH/repo/.git/logs/HEAD"
mkdir -p "$SCRATCH/repo/sub"
ok "one commit inside [1787263500, 1787264000], found from a SUBdirectory" \
  "python3 -c \"import transcripto as t; c=t._reflog_commits('$SCRATCH/repo/sub',1787263500,1787264000); assert [x['sha'] for x in c]==['bbbbbbb'], c; assert c[0]['subject']=='inside the window'\""
ok "a rebase pick is not a commit; the open window counts 3" \
  "python3 -c \"import transcripto as t; assert len(t._reflog_commits('$SCRATCH/repo'))==3\""
ok "not a repo -> None (never 0)" \
  "python3 -c \"import transcripto as t; assert t._reflog_commits('$SCRATCH/nowhere-such-dir') is None\""
ok "still no subprocess / socket / urllib in the file" \
  "! grep -nE '\\b(socket|urllib|requests|http\\.client|subprocess)\\b' transcripto.py"
rm -rf "$SCRATCH"

echo
if [ "$FAIL" -eq 0 ]; then echo "$PASS/$((PASS+FAIL)) green."; else echo "$PASS/$((PASS+FAIL)) — $FAIL RED."; exit 1; fi
