#!/usr/bin/env bash
# cold_verify.sh — stranger one-command path for the retention METHOD.
#
# Object: file ages under a projects root. NOT authorship / human_turns.
#   find "$ROOT" -name '*.jsonl' | wc -l
#   find "$ROOT" -name '*.jsonl' ! -newermt <30d> | wc -l
#
# Oscar's frozen quote (2026-08-28): 504 of 2,721 files older than 30 days.
# This VM usually has no ~/.claude/projects. When live corpus is absent, we
# generate an arithmetic-faithful fixture (2721 files, 504 aged 31–44d so
# older_than_45d stays 0) and assert exact counts. Live Oscar numbers are NOT
# re-derived here — they remain a machine-local quote.
#
# Ambition beyond planter/assert: an INDEPENDENT find↔stat oracle plants a
# blind age set (no shared 504/2721 target) and checks find against Python
# mtime. A fixture that plants N and asserts N only proves the planter.
#
# Usage: bash scripts/cold_verify.sh
# Optional: TRANSCRIPTO_COLD_DIR=/path  keep work dir for inspection
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

KEEP_WORK=0
if [ -n "${TRANSCRIPTO_COLD_DIR:-}" ]; then
  WORK="$TRANSCRIPTO_COLD_DIR"
  mkdir -p "$WORK"
  KEEP_WORK=1
else
  WORK="$(mktemp -d /tmp/transcripto-cold-verify-XXXXXX)"
fi
VENV="$WORK/venv"
FAIL=0

cleanup() {
  if [ "$KEEP_WORK" -eq 0 ]; then
    rm -rf "$WORK"
  else
    echo "work dir kept: $WORK"
  fi
}
trap cleanup EXIT

echo "=== COLD VERIFY · $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "repo: $REPO_ROOT"
echo "work: $WORK"
echo

# --- fresh venv, no network after install-from-source ---
python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install -U pip -q
python -m pip install -e "$REPO_ROOT" -q
echo "transcripto: $(transcripto --version 2>/dev/null || python -c 'import transcripto; print(getattr(transcripto,\"VERSION\", \"?\"))')"
echo

# --- retention root: live corpus or arithmetic fixture ---
LIVE_ROOT="$HOME/.claude/projects"
FIXTURE_ROOT="$WORK/fixtures-retention-504-of-2721"
MODE=""

setup_retention_504_of_2721() {
  # Exact arithmetic of the frozen quote. Ages 31–44d so 45d count stays 0.
  local root="$1"
  local proj="$root/demo-project/sessions"
  mkdir -p "$proj"
  local i
  echo "generating fixture: 2721 jsonl files (504 aged 31–44d)…"
  for i in $(seq 0 2720); do
    printf '%s\n' \
      '{"type":"user","promptSource":"typed","message":{"role":"user","content":"fixture turn"}}' \
      > "$proj/session-$(printf '%04d' "$i").jsonl"
  done
  # Touch first 504 to ages 31..44 days ago (cycle 14-day window).
  for i in $(seq 0 503); do
    local days=$((31 + (i % 14)))
    touch -d "$days days ago" "$proj/session-$(printf '%04d' "$i").jsonl"
  done
}

if [ -d "$LIVE_ROOT" ] && find "$LIVE_ROOT" -name '*.jsonl' -print -quit 2>/dev/null | grep -q .; then
  ROOT="$LIVE_ROOT"
  MODE="live"
  echo "retention source: LIVE $ROOT"
else
  setup_retention_504_of_2721 "$FIXTURE_ROOT"
  ROOT="$FIXTURE_ROOT"
  MODE="fixture"
  echo "retention source: FIXTURE $ROOT"
  echo "  (no live ~/.claude/projects on this machine — method + arithmetic only)"
fi
echo

# --- measure at the file object (re-derive; do not carry) ---
THIRTY=$(date -d '30 days ago' +%Y-%m-%d)
FORTYFIVE=$(date -d '45 days ago' +%Y-%m-%d)
TOTAL=$(find "$ROOT" -name '*.jsonl' | wc -l | tr -d ' ')
OLD30=$(find "$ROOT" -name '*.jsonl' ! -newermt "$THIRTY" | wc -l | tr -d ' ')
OLD45=$(find "$ROOT" -name '*.jsonl' ! -newermt "$FORTYFIVE" | wc -l | tr -d ' ')

# oldest file — avoid SIGPIPE under pipefail (do not pipe find|head)
OLDEST_FILE=""
OLDEST_EPOCH=""
while IFS= read -r -d '' f; do
  e=$(stat -c %Y "$f" 2>/dev/null || echo "")
  if [ -n "$e" ]; then
    if [ -z "$OLDEST_EPOCH" ] || [ "$e" -lt "$OLDEST_EPOCH" ]; then
      OLDEST_EPOCH=$e
      OLDEST_FILE=$f
    fi
  fi
done < <(find "$ROOT" -name '*.jsonl' -print0)

echo "=== RETENTION (find method, re-derived) ==="
echo "mode: $MODE"
echo "as_of: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "threshold_30d: mtime <= $THIRTY"
echo "threshold_45d: mtime <= $FORTYFIVE"
echo "total_jsonl: $TOTAL"
echo "older_than_30d: $OLD30"
echo "older_than_45d: $OLD45"
echo "ratio_30d: $OLD30 of $TOTAL"
if [ -n "$OLDEST_FILE" ]; then
  echo "oldest_file: $OLDEST_FILE"
  echo "oldest_mtime: $(date -u -d "@$OLDEST_EPOCH" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || true)"
fi
echo
echo "frozen_quote (Oscar 2026-08-28, NOT re-derived on this VM unless mode=live): 504 of 2,721"
echo "frozen_rederive (Oscar 2026-08-29, NOT re-derived here): 579 of 2,874"
echo "NOTE: the two frozen stamps do not reconcile by arithmetic; no daily death rate is claimed."
echo

if [ "$MODE" = "fixture" ]; then
  if [ "$TOTAL" = "2721" ] && [ "$OLD30" = "504" ] && [ "$OLD45" = "0" ]; then
    echo "ASSERT fixture 504 of 2721 (old45=0): PASS"
  else
    echo "ASSERT fixture 504 of 2721 (old45=0): FAIL (got $OLD30 of $TOTAL, old45=$OLD45)"
    FAIL=1
  fi
else
  echo "ASSERT live: reported only — compare to frozen quotes by hand; no exact equality required."
fi
echo

# --- INDEPENDENT ORACLE: blind ages, find vs Python mtime (no shared 504/2721) ---
# A planter that asserts its own plant proves nothing about find. This section
# draws ages 0..60 days for 180 files, computes expected counts from st_mtime
# against the same calendar thresholds, and compares to find ! -newermt.
echo "=== INDEPENDENT ORACLE (find ↔ Python mtime, blind ages) ==="
ORACLE_ROOT="$WORK/oracle-blind-ages"
mkdir -p "$ORACLE_ROOT"
set +e
ORACLE_REPORT=$(THIRTY="$THIRTY" FORTYFIVE="$FORTYFIVE" ORACLE_ROOT="$ORACLE_ROOT" python - <<'PY'
import os, random, subprocess, time
from datetime import datetime
from pathlib import Path

root = Path(os.environ["ORACLE_ROOT"])
thirty = os.environ["THIRTY"]
fortyfive = os.environ["FORTYFIVE"]
# Parse thresholds the same way GNU find -newermt DATE does for YYYY-MM-DD:
# start of that local calendar day.
def day_start(ymd: str) -> float:
    return datetime.strptime(ymd, "%Y-%m-%d").timestamp()

t30 = day_start(thirty)
t45 = day_start(fortyfive)
rng = random.Random(20260906)  # reproducible, not the retention quote
n = 180
ages = [rng.randint(0, 60) for _ in range(n)]
now = time.time()
for i, days in enumerate(ages):
    p = root / ("blind-%03d.jsonl" % i)
    p.write_text('{"type":"user","message":{"role":"user","content":"oracle"}}\n')
    os.utime(p, (now - days * 86400, now - days * 86400))

def expect(threshold: float) -> int:
    # GNU find -newermt DATE ⇒ mtime > reference (local midnight for YYYY-MM-DD).
    # ! -newermt ⇒ mtime <= midnight. Files at exactly midnight are counted.
    c = 0
    for p in root.glob("*.jsonl"):
        if p.stat().st_mtime <= threshold:
            c += 1
    return c

exp30 = expect(t30)
exp45 = expect(t45)

def find_count(ymd: str) -> int:
    out = subprocess.check_output(
        ["bash", "-lc", f"find '{root}' -name '*.jsonl' ! -newermt '{ymd}' | wc -l"],
        text=True,
    )
    return int(out.strip())

f30 = find_count(thirty)
f45 = find_count(fortyfive)
total = len(list(root.glob("*.jsonl")))
print(f"oracle_files: {total}")
print(f"oracle_age_days_min_max: {min(ages)} {max(ages)}")
print(f"oracle_python_old30: {exp30}")
print(f"oracle_find_old30: {f30}")
print(f"oracle_python_old45: {exp45}")
print(f"oracle_find_old45: {f45}")
print(f"threshold_30d_epoch: {t30}")
print(f"threshold_45d_epoch: {t45}")
ok = exp30 == f30 and exp45 == f45 and total == n
print("independent_oracle: PASS" if ok else "independent_oracle: FAIL")
raise SystemExit(0 if ok else 1)
PY
)
oracle_rc=$?
set -e
printf '%s\n' "$ORACLE_REPORT"
if [ "$oracle_rc" -ne 0 ]; then
  FAIL=1
fi
echo

# --- BOUNDARY probe: file exactly at midnight of THIRTY / one second after ---
echo "=== BOUNDARY PROBE (exactly at threshold) ==="
BOUND="$WORK/boundary"
mkdir -p "$BOUND"
# Reference midnight local for THIRTY
REF_EPOCH=$(date -d "$THIRTY 00:00:00" +%s)
touch -d "@$REF_EPOCH" "$BOUND/at-midnight.jsonl"
touch -d "@$((REF_EPOCH + 1))" "$BOUND/one-sec-after.jsonl"
touch -d "@$((REF_EPOCH - 1))" "$BOUND/one-sec-before.jsonl"
printf '%s\n' '{"k":1}' > "$BOUND/at-midnight.jsonl"
printf '%s\n' '{"k":1}' > "$BOUND/one-sec-after.jsonl"
printf '%s\n' '{"k":1}' > "$BOUND/one-sec-before.jsonl"
# re-touch after write (write updates mtime)
touch -d "@$REF_EPOCH" "$BOUND/at-midnight.jsonl"
touch -d "@$((REF_EPOCH + 1))" "$BOUND/one-sec-after.jsonl"
touch -d "@$((REF_EPOCH - 1))" "$BOUND/one-sec-before.jsonl"
AT=$(find "$BOUND" -name 'at-midnight.jsonl' ! -newermt "$THIRTY" | wc -l | tr -d ' ')
AFTER=$(find "$BOUND" -name 'one-sec-after.jsonl' ! -newermt "$THIRTY" | wc -l | tr -d ' ')
BEFORE=$(find "$BOUND" -name 'one-sec-before.jsonl' ! -newermt "$THIRTY" | wc -l | tr -d ' ')
echo "threshold_midnight_epoch: $REF_EPOCH ($THIRTY 00:00:00 local)"
echo "counted_by_bang_newermt at_midnight: $AT   (expect 1 — mtime == ref is NOT newer)"
echo "counted_by_bang_newermt one_sec_after: $AFTER   (expect 0 — strictly newer)"
echo "counted_by_bang_newermt one_sec_before: $BEFORE   (expect 1)"
if [ "$AT" = "1" ] && [ "$AFTER" = "0" ] && [ "$BEFORE" = "1" ]; then
  echo "boundary_probe: PASS — ! -newermt means mtime <= threshold midnight"
else
  echo "boundary_probe: FAIL — unexpected inclusion (at=$AT after=$AFTER before=$BEFORE)"
  FAIL=1
fi
# Calendar threshold ≠ pure duration. A file aged exactly 30*86400 seconds may
# still be NEWER than calendar midnight of "30 days ago" (same calendar day,
# later clock time) and therefore NOT counted by ! -newermt.
DUR="$WORK/duration-vs-calendar"
mkdir -p "$DUR"
DUR_EPOCH=$(( $(date +%s) - 30*86400 ))
printf '%s\n' '{"k":1}' > "$DUR/exactly-30d-duration.jsonl"
touch -d "@$DUR_EPOCH" "$DUR/exactly-30d-duration.jsonl"
DUR_COUNTED=$(find "$DUR" -name 'exactly-30d-duration.jsonl' ! -newermt "$THIRTY" | wc -l | tr -d ' ')
echo "duration_vs_calendar: file aged exactly 30*86400s counted_by_bang_newermt=$DUR_COUNTED"
echo "  (0 means calendar method is stricter than pure duration at this clock time;"
echo "   1 means the duration-aged file already sits on/before threshold midnight)"
echo "caveat: article find method uses calendar midnight, not age_seconds > 30*86400"
echo

# --- deletion-timer control: must be watchable RED ---
# Missing settings.json → grep finds nothing. With set -e this would abort;
# we capture the exit explicitly. Empty/missing must NOT read as "timer off".
echo "=== DELETION TIMER PROBE ==="
SETTINGS="${HOME}/.claude/settings.json"
if [ -f "$SETTINGS" ]; then
  set +e
  grep -n 'cleanupPeriodDays' "$SETTINGS"
  greprc=$?
  set -e
  echo "grep_cleanupPeriodDays_exit: $greprc"
  if [ "$greprc" -eq 0 ]; then
    echo "timer_key: present (value is whatever grep printed above — re-read the file)"
  else
    echo "timer_key: ABSENT — Claude Code default cleanupPeriodDays=30 applies (docs)."
    echo "control_note: absence means the timer is ON at default, not off."
  fi
else
  set +e
  grep -n 'cleanupPeriodDays' /nonexistent-transcripto-settings-$$ 2>/dev/null
  greprc=$?
  set -e
  echo "settings.json: missing"
  echo "grep_cleanupPeriodDays_exit: $greprc  (watched RED / nonzero on missing file)"
  echo "control_note: no settings file → default 30-day cleanup applies per Claude Code docs."
  if [ "$greprc" -eq 0 ]; then
    echo "CONTROL FAIL: grep returned 0 on missing settings — green-on-outage trap"
    FAIL=1
  else
    echo "control_watched_red: PASS"
  fi
fi
# Re-derive default from the settings-reference object (not memory).
set +e
DOCS_MD=$(curl -fsSL --max-time 20 -A 'Mozilla/5.0' \
  https://code.claude.com/docs/en/settings-reference.md 2>/dev/null)
docs_rc=$?
set -e
if [ "$docs_rc" -eq 0 ] && [ -n "$DOCS_MD" ]; then
  echo "docs_object: https://code.claude.com/docs/en/settings-reference.md"
  DEF=$(printf '%s\n' "$DOCS_MD" | awk '
    /^### `cleanupPeriodDays`/ {insec=1; next}
    /^### / {if(insec) exit}
    insec && /^\* \*\*Default\*\*:/ {print; exit}
  ')
  DDEF=$(printf '%s\n' "$DOCS_MD" | awk '
    /^### `desktopSessionCleanupPeriodDays`/ {insec=1; next}
    /^### / {if(insec) exit}
    insec && /^\* \*\*Default\*\*:/ {print; exit}
  ')
  echo "cleanupPeriodDays_default_line: $DEF"
  echo "desktopSessionCleanupPeriodDays_default_line: $DDEF"
  if printf '%s' "$DEF" | grep -q '`30`'; then
    echo "docs_cleanupPeriodDays_default_30: PASS (re-derived from settings-reference.md)"
  else
    echo "docs_cleanupPeriodDays_default_30: FAIL (got: $DEF)"
    FAIL=1
  fi
  if printf '%s' "$DDEF" | grep -q '`0`'; then
    echo "docs_desktop_default_0_no_age_limit: PASS"
  else
    echo "docs_desktop_default_0_no_age_limit: not confirmed (got: $DDEF)"
  fi
else
  echo "docs_object_fetch: SKIP (curl exit $docs_rc) — do not carry a default from memory"
fi
echo

# --- anti-conflation: one file with 2721 records is NOT 2721 files ---
echo "=== ANTI-CONFLATION (wrong object must not look like retention) ==="
BAD="$WORK/wrong-object-authorship-gate"
mkdir -p "$BAD"
python - <<PY
from pathlib import Path
p = Path("$BAD") / "retention-gate.jsonl"
HUMAN, TOTAL = 504, 2721
lines = []
for i in range(HUMAN):
    lines.append('{"type":"user","promptSource":"typed","message":{"role":"user","content":"turn %d"}}' % i)
while len(lines) < TOTAL:
    # disguised non-human user rows — looks like type:user to a naive counter
    lines.append('{"type":"user","toolUseResult":{"ok":true},"message":{"role":"user","content":"tool result"}}')
p.write_text("\n".join(lines) + "\n")
print("wrote", TOTAL, "records into", p)
PY
BAD_FILES=$(find "$BAD" -name '*.jsonl' | wc -l | tr -d ' ')
BAD_OLD=$(find "$BAD" -name '*.jsonl' ! -newermt "$THIRTY" | wc -l | tr -d ' ')
BAD_RECORDS=$(wc -l < "$BAD/retention-gate.jsonl" | tr -d ' ')
echo "wrong_object_files: $BAD_FILES"
echo "wrong_object_records: $BAD_RECORDS"
echo "wrong_object_old30_files: $BAD_OLD"
if [ "$BAD_FILES" = "1" ] && [ "$BAD_RECORDS" = "2721" ]; then
  echo "anti_conflation: PASS — 2721 records in 1 file ≠ 2721 files (retention object)"
else
  echo "anti_conflation: FAIL — expected 1 file / 2721 records, got files=$BAD_FILES records=$BAD_RECORDS"
  FAIL=1
fi
echo

# --- STEP 0 small-n gate (separate product control) ---
echo "=== STEP 0 · small-n gate ==="
set +e
STEP0_OUT=$(bash "$REPO_ROOT/scripts/test_small_n.sh" 2>&1)
step0rc=$?
set -e
printf '%s\n' "$STEP0_OUT"
if [ "$step0rc" -ne 0 ]; then
  echo "STEP 0: FAIL"
  FAIL=1
else
  echo "STEP 0: PASS"
fi
echo

# --- authorship baseline (SEPARATE object from retention) ---
echo "=== AUTHORSHIP GATE (fixtures-coach) — not the retention story ==="
COACH_ROOT="$REPO_ROOT/fixtures-coach"
read -r NAIVE TOTAL_REC_NAIVE <<EOF
$(python - <<PY
import json
from pathlib import Path
n=0; t=0
for line in Path("$COACH_ROOT").joinpath("coach-fixture.jsonl").read_text().splitlines():
    if not line.strip():
        continue
    t += 1
    d = json.loads(line)
    if d.get("type") == "user":
        n += 1
print(n, t)
PY
)
EOF
GATE_JSON=$(python "$REPO_ROOT/transcripto.py" coach --root "$COACH_ROOT" --json 2>/dev/null)
GATE=$(printf '%s' "$GATE_JSON" | python -c "import json,sys; print(json.load(sys.stdin)['human_turns'])")
TOTAL_REC=$(printf '%s' "$GATE_JSON" | python -c "import json,sys; print(json.load(sys.stdin)['total_records'])")
echo "naive type:user count: $NAIVE"
echo "transcripto human_turns (gated): $GATE"
echo "total_records: $TOTAL_REC (naive line scan saw $TOTAL_REC_NAIVE)"
if [ "$NAIVE" -gt "$GATE" ]; then
  echo "baseline: naive overcounts (gate is stricter) — expected"
else
  echo "baseline: unexpected (naive=$NAIVE gate=$GATE)"
  FAIL=1
fi
echo

# --- privacy: real tree must pass; empty index must FAIL (control watched RED) ---
echo "=== PRIVACY ==="
set +e
PRIV_OUT=$(bash "$REPO_ROOT/test_privacy.sh" 2>&1)
privrc=$?
set -e
printf '%s\n' "$PRIV_OUT"
if [ "$privrc" -ne 0 ]; then
  echo "privacy on real tree: FAIL"
  FAIL=1
else
  echo "privacy on real tree: PASS"
fi
EMPTY_DIR="$WORK/privacy-empty-index"
rm -rf "$EMPTY_DIR"
mkdir -p "$EMPTY_DIR"
(
  cd "$EMPTY_DIR"
  git init -q
  cp "$REPO_ROOT/test_privacy.sh" .
  set +e
  OUT=$(bash test_privacy.sh 2>&1)
  rc=$?
  set -e
  printf '%s\n' "$OUT"
  echo "privacy_empty_index_exit: $rc"
  if [ "$rc" -eq 0 ]; then
    echo "CONTROL FAIL: privacy green on empty git index"
    exit 1
  else
    echo "privacy_empty_index_watched_red: PASS"
  fi
) || FAIL=1
echo

# --- regression suites (product still works cold) ---
echo "=== SUITES ==="
for t in test_coach.sh test_codex.sh test_cost.sh test_label_bands.sh test_small_n.sh test_cursor_partial.sh test_correction.sh test_version.sh; do
  if [ -f "$REPO_ROOT/$t" ]; then
    set +e
    out=$(bash "$REPO_ROOT/$t" 2>&1)
    rc=$?
    set -e
    tail_line=$(printf '%s\n' "$out" | tail -1)
    echo "$t → exit $rc · $tail_line"
    if [ "$rc" -ne 0 ]; then
      FAIL=1
    fi
  fi
done
echo

if [ "$FAIL" -eq 0 ]; then
  echo "cold_verify: PASS"
  exit 0
else
  echo "cold_verify: FAIL"
  exit 1
fi
