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
# Ambition beyond planter/assert (tonight 2026-09-11):
#   1. INDEPENDENT find↔stat oracle (blind ages; no shared 504/2721 target).
#   2. NEGATIVE PLANTER that must go RED (wrong plant must fail the assert).
#   3. OFFLINE CORE after source install — proxy poisoned so accidental
#      network cannot paint retention green.
#   4. MULTI-TZ divergence probe (UTC/LA/Tokyo/London — pair trap watched).
#   5. stats near-miss detector (message counts ≠ file-age retention).
#   6. NETWORK PROBES (docs/PyPI) are separate; SKIP must not mean PASS.
#   7. Oracle must not accidentally equal 504/2721 (carry/collision guard).
#   8. FROZEN-QUOTE NON-RECONCILIATION — two stamps ≠ unique death rate.
#   9. CALENDAR↔DURATION DELTA on the full planted fixture (not one file).
#  10. TOUCH↔UTIME planter agreement (shell touch -d vs os.utime).
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
OFFLINE_CORE_FAIL=0

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

# --- fresh venv from source (network may be needed once for pip/setuptools) ---
python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
# Prefer offline editable install; fall back to one network attempt for pip bootstrap.
set +e
python -m pip install -e "$REPO_ROOT" --no-deps -q 2>"$WORK/pip-offline.err"
pip_rc=$?
set -e
if [ "$pip_rc" -ne 0 ]; then
  echo "pip offline editable failed; one network bootstrap attempt…"
  python -m pip install -U pip -q
  python -m pip install -e "$REPO_ROOT" -q
fi
echo "transcripto: $(transcripto --version 2>/dev/null || python -c 'import transcripto; print(getattr(transcripto,\"VERSION\", \"?\"))')"
echo

# Poison proxies for the OFFLINE CORE. Docs/PyPI probes restore later.
export HTTP_PROXY=http://127.0.0.1:9
export HTTPS_PROXY=http://127.0.0.1:9
export ALL_PROXY=http://127.0.0.1:9
export NO_PROXY=
echo "=== OFFLINE CORE (proxies poisoned to 127.0.0.1:9) ==="
echo

# --- retention root: live corpus or arithmetic fixture ---
LIVE_ROOT="$HOME/.claude/projects"
FIXTURE_ROOT="$WORK/fixtures-retention-504-of-2721"
MODE=""

plant_retention_fixture() {
  # Args: root total_files old_count
  # Ages 31–44d so 45d count stays 0 when old_count files are aged.
  local root="$1"
  local total="$2"
  local old="$3"
  FIXTURE_ROOT="$root" FIXTURE_TOTAL="$total" FIXTURE_OLD="$old" python - <<'PY'
import os, time
from pathlib import Path
root = Path(os.environ["FIXTURE_ROOT"]) / "demo-project" / "sessions"
root.mkdir(parents=True, exist_ok=True)
total = int(os.environ["FIXTURE_TOTAL"])
old = int(os.environ["FIXTURE_OLD"])
now = time.time()
body = b'{"type":"user","promptSource":"typed","message":{"role":"user","content":"fixture turn"}}\n'
for i in range(total):
    p = root / ("session-%04d.jsonl" % i)
    p.write_bytes(body)
    if i < old:
        days = 31 + (i % 14)
        ts = now - days * 86400
        os.utime(p, (ts, ts))
print("fixture_files_written: %d old_planted: %d" % (total, old))
PY
}

setup_retention_504_of_2721() {
  echo "generating fixture: 2721 jsonl files (504 aged 31–44d)…"
  plant_retention_fixture "$1" 2721 504
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
    OFFLINE_CORE_FAIL=1
  fi
else
  echo "ASSERT live: reported only — compare to frozen quotes by hand; no exact equality required."
fi
echo

# --- NEGATIVE PLANTER: wrong plant MUST fail the 504/2721 assert (watched RED) ---
echo "=== NEGATIVE PLANTER (must go RED — control that can fail) ==="
NEG_ROOT="$WORK/fixtures-retention-WRONG-503-of-2720"
plant_retention_fixture "$NEG_ROOT" 2720 503
NEG_TOTAL=$(find "$NEG_ROOT" -name '*.jsonl' | wc -l | tr -d ' ')
NEG_OLD=$(find "$NEG_ROOT" -name '*.jsonl' ! -newermt "$THIRTY" | wc -l | tr -d ' ')
echo "negative_plant: $NEG_OLD of $NEG_TOTAL (deliberately not 504 of 2721)"
if [ "$NEG_TOTAL" = "2721" ] && [ "$NEG_OLD" = "504" ]; then
  echo "negative_planter: FAIL — wrong plant accidentally matched 504/2721"
  FAIL=1
  OFFLINE_CORE_FAIL=1
else
  echo "negative_planter_assert_would_reject: YES (got $NEG_OLD of $NEG_TOTAL)"
  echo "negative_planter: PASS — watched RED (wrong plant does not satisfy 504/2721)"
fi
echo

# --- INDEPENDENT ORACLE: blind ages, find vs Python mtime (no shared 504/2721) ---
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

def day_start(ymd: str) -> float:
    return datetime.strptime(ymd, "%Y-%m-%d").timestamp()

t30 = day_start(thirty)
t45 = day_start(fortyfive)
rng = random.Random(20260911)  # reproducible tonight; not the retention quote
n = 180
ages = [rng.randint(0, 60) for _ in range(n)]
now = time.time()
for i, days in enumerate(ages):
    p = root / ("blind-%03d.jsonl" % i)
    p.write_text('{"type":"user","message":{"role":"user","content":"oracle"}}\n')
    os.utime(p, (now - days * 86400, now - days * 86400))

def expect(threshold: float) -> int:
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
# Collision guard: oracle must not look like the retention quote.
collision = total == 2721 or f30 == 504 or (f30 == 504 and total == 2721)
if collision:
    print("oracle_retention_collision: FAIL — blind oracle matched 504/2721 shape")
ok = exp30 == f30 and exp45 == f45 and total == n and not collision
print("independent_oracle: PASS" if ok else "independent_oracle: FAIL")
raise SystemExit(0 if ok else 1)
PY
)
oracle_rc=$?
set -e
printf '%s\n' "$ORACLE_REPORT"
if [ "$oracle_rc" -ne 0 ]; then
  FAIL=1
  OFFLINE_CORE_FAIL=1
fi
echo

# --- BOUNDARY probe ---
echo "=== BOUNDARY PROBE (exactly at threshold) ==="
BOUND="$WORK/boundary"
mkdir -p "$BOUND"
REF_EPOCH=$(date -d "$THIRTY 00:00:00" +%s)
printf '%s\n' '{"k":1}' > "$BOUND/at-midnight.jsonl"
printf '%s\n' '{"k":1}' > "$BOUND/one-sec-after.jsonl"
printf '%s\n' '{"k":1}' > "$BOUND/one-sec-before.jsonl"
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
  OFFLINE_CORE_FAIL=1
fi
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

# --- FULL FIXTURE calendar↔duration delta (beyond floor: open the whole object) ---
# Prior waves only probed ONE duration-aged file. Tonight count every planted
# file under both methods. A silent disagreement is the embarrassment.
echo "=== CALENDAR↔DURATION DELTA (full retention root) ==="
DELTA_OUT=$(ROOT="$ROOT" THIRTY="$THIRTY" REF_EPOCH="$REF_EPOCH" python - <<'PY'
import os
from pathlib import Path
root = Path(os.environ["ROOT"])
ref = float(os.environ["REF_EPOCH"])  # calendar midnight of "30 days ago"
now = __import__("time").time()
dur_cut = now - 30 * 86400
cal = dur = both = cal_only = dur_only = 0
for p in root.rglob("*.jsonl"):
    m = p.stat().st_mtime
    c = m <= ref
    d = m <= dur_cut
    if c:
        cal += 1
    if d:
        dur += 1
    if c and d:
        both += 1
    elif c:
        cal_only += 1
    elif d:
        dur_only += 1
print(f"calendar_old30: {cal}")
print(f"duration_old30: {dur}")
print(f"both_methods: {both}")
print(f"calendar_only: {cal_only}")
print(f"duration_only: {dur_only}")
print(f"ref_calendar_epoch: {ref:.0f}")
print(f"ref_duration_epoch: {dur_cut:.0f}")
print(f"method_skew_seconds: {abs(ref - dur_cut):.0f}")
disagree = cal_only + dur_only
if disagree:
    print(f"calendar_duration_delta: OBSERVED — {disagree} files disagree (cal_only={cal_only} dur_only={dur_only})")
    print("calendar_duration_ruling: publishing either method without naming it conflates two cuts")
else:
    print("calendar_duration_delta: none tonight — both methods agree on this root at this clock")
# Informational: does not fail cold_verify unless counting exploded.
print("calendar_duration_probe: PASS")
PY
)
printf '%s\n' "$DELTA_OUT"
if ! printf '%s\n' "$DELTA_OUT" | grep -q 'calendar_duration_probe: PASS'; then
  echo "calendar_duration_probe: FAIL"
  FAIL=1
  OFFLINE_CORE_FAIL=1
fi
echo

# --- TOUCH↔UTIME planter agreement (beyond floor) ---
# Plant the same nominal ages two ways. If find counts disagree, the fixture
# method itself is the bug — not the retention story.
echo "=== TOUCH↔UTIME PLANTER (shell touch -d vs os.utime) ==="
TU_ROOT="$WORK/touch-vs-utime"
mkdir -p "$TU_ROOT/touch" "$TU_ROOT/utime"
# Ten shared age offsets (days), including near the 30d boundary.
AGES="28 29 30 31 32 33 40 44 45 50"
i=0
for days in $AGES; do
  i=$((i + 1))
  # Shell touch: date string relative to now (GNU touch).
  printf '%s\n' '{"k":1}' > "$TU_ROOT/touch/age-$i.jsonl"
  touch -d "$days days ago" "$TU_ROOT/touch/age-$i.jsonl"
  # Python utime: exact now - days*86400 (matches the cold fixture planter).
  DAYS="$days" PATH_U="$TU_ROOT/utime/age-$i.jsonl" python - <<'PY'
import os, time
from pathlib import Path
p = Path(os.environ["PATH_U"])
p.write_text('{"k":1}\n')
ts = time.time() - int(os.environ["DAYS"]) * 86400
os.utime(p, (ts, ts))
PY
done
TOUCH_OLD=$(find "$TU_ROOT/touch" -name '*.jsonl' ! -newermt "$THIRTY" | wc -l | tr -d ' ')
UTIME_OLD=$(find "$TU_ROOT/utime" -name '*.jsonl' ! -newermt "$THIRTY" | wc -l | tr -d ' ')
TOUCH_N=$(find "$TU_ROOT/touch" -name '*.jsonl' | wc -l | tr -d ' ')
UTIME_N=$(find "$TU_ROOT/utime" -name '*.jsonl' | wc -l | tr -d ' ')
echo "touch_planter_old30: $TOUCH_OLD of $TOUCH_N"
echo "utime_planter_old30: $UTIME_OLD of $UTIME_N"
echo "ages_days: $AGES"
echo "threshold_30d: $THIRTY"
if [ "$TOUCH_N" != "10" ] || [ "$UTIME_N" != "10" ]; then
  echo "touch_utime_planter: FAIL — expected 10 files each"
  FAIL=1
  OFFLINE_CORE_FAIL=1
elif [ "$TOUCH_OLD" = "$UTIME_OLD" ]; then
  echo "touch_utime_planter: PASS — find counts agree ($TOUCH_OLD)"
else
  # Disagreement is an embarrassment finding: calendar 'N days ago' via touch
  # is not the same object as now-N*86400 via utime (local midnight vs duration).
  echo "touch_utime_planter: DIVERGENCE — touch_old=$TOUCH_OLD utime_old=$UTIME_OLD"
  echo "touch_utime_ruling: fixture planter must name which age object it uses"
  echo "touch_utime_planter: PASS (divergence watched; cold fixture uses os.utime)"
fi
echo

# --- TZ divergence: calendar cut can disagree across TZ ---
# Bigger object than UTC↔LA alone: at some clock times those two agree while
# Asia/Tokyo (or others) still disagree. Watch a set, not a pair.
echo "=== TZ DIVERGENCE PROBE (multi-zone calendar cut) ==="
TZ_ROOT="$WORK/tz-probe"
mkdir -p "$TZ_ROOT"
NEAR_EPOCH=$(( $(date +%s) - 30*86400 + 3600 ))
printf '%s\n' '{"k":1}' > "$TZ_ROOT/near-boundary.jsonl"
touch -d "@$NEAR_EPOCH" "$TZ_ROOT/near-boundary.jsonl"
UTC_THIRTY=$(TZ=UTC date -d '30 days ago' +%Y-%m-%d)
LA_THIRTY=$(TZ=America/Los_Angeles date -d '30 days ago' +%Y-%m-%d)
TOKYO_THIRTY=$(TZ=Asia/Tokyo date -d '30 days ago' +%Y-%m-%d)
LONDON_THIRTY=$(TZ=Europe/London date -d '30 days ago' +%Y-%m-%d)
UTC_COUNT=$(TZ=UTC find "$TZ_ROOT" -name '*.jsonl' ! -newermt "$UTC_THIRTY" | wc -l | tr -d ' ')
LA_COUNT=$(TZ=America/Los_Angeles find "$TZ_ROOT" -name '*.jsonl' ! -newermt "$LA_THIRTY" | wc -l | tr -d ' ')
TOKYO_COUNT=$(TZ=Asia/Tokyo find "$TZ_ROOT" -name '*.jsonl' ! -newermt "$TOKYO_THIRTY" | wc -l | tr -d ' ')
LONDON_COUNT=$(TZ=Europe/London find "$TZ_ROOT" -name '*.jsonl' ! -newermt "$LONDON_THIRTY" | wc -l | tr -d ' ')
echo "tz_utc_threshold: $UTC_THIRTY counted=$UTC_COUNT"
echo "tz_la_threshold: $LA_THIRTY counted=$LA_COUNT"
echo "tz_tokyo_threshold: $TOKYO_THIRTY counted=$TOKYO_COUNT"
echo "tz_london_threshold: $LONDON_THIRTY counted=$LONDON_COUNT"
echo "tz_local_threshold: $THIRTY"
TZ_SET="$UTC_THIRTY $LA_THIRTY $TOKYO_THIRTY $LONDON_THIRTY"
TZ_UNIQ=$(printf '%s\n' $TZ_SET | sort -u | wc -l | tr -d ' ')
if [ "$TZ_UNIQ" -gt 1 ]; then
  echo "tz_divergence: OBSERVED — $TZ_UNIQ distinct calendar cuts tonight; publish TZ with the figure"
  if [ "$UTC_THIRTY" = "$LA_THIRTY" ] && [ "$UTC_THIRTY" != "$TOKYO_THIRTY" ]; then
    echo "tz_pair_trap: DETECTED — UTC↔LA agree ($UTC_THIRTY) while Tokyo differs ($TOKYO_THIRTY)"
    echo "tz_pair_trap_ruling: a two-zone probe can miss divergence that a third zone catches"
  fi
else
  echo "tz_divergence: none at this clock (all four thresholds: $UTC_THIRTY); still document TZ with live figures"
fi
echo "tz_probe: PASS (informational; does not fail cold_verify)"
echo

# --- Frozen-quote non-reconciliation (embarrassment: no unique daily death rate) ---
# Oscar stamps (NOT re-derived on this VM): 504/2721 (2026-08-28) and
# 579/2874 (2026-08-29). Both numerator and denominator moved. A unique
# "files die at N/day" claim is not entailed.
echo "=== FROZEN-QUOTE NON-RECONCILIATION (no unique death rate) ==="
FROZEN_OUT=$(python - <<'PY'
# Stamps are labels of two machine-local quotes. Arithmetic only — no live corpus.
a_old, a_tot = 504, 2721
b_old, b_tot = 579, 2874
d_old, d_tot = b_old - a_old, b_tot - a_tot
print(f"frozen_a_2026-08-28: {a_old} of {a_tot}")
print(f"frozen_b_2026-08-29: {b_old} of {b_tot}")
print(f"delta_old: {d_old:+d}")
print(f"delta_total: {d_tot:+d}")
# Model 1: only young files added (no deletions, no aging into the old bucket).
# Then old count must stay flat. Observed old rose → rejected.
m1 = "REJECTED" if d_old != 0 else "compatible"
print(f"model_only_young_additions: {m1} (predicts delta_old=0; got {d_old:+d})")
# Model 2: only aging (no create/delete). Total flat; some files cross 30d.
m2 = "REJECTED" if d_tot != 0 else "compatible"
print(f"model_only_aging_no_churn: {m2} (predicts delta_total=0; got {d_tot:+d})")
# Model 3: unique daily death rate d such that old_{t+1}=old_t - d + aged_in,
# with aged_in unknown and creates/deletes unknown — infinite solutions.
print("model_unique_daily_death_rate: UNDERDETERMINED (aged_in, creates, deletes free)")
print("frozen_quote_reconcile: FAIL-TO-RECONCILE — no unique death rate from two stamps alone")
print("frozen_quote_ruling: do not print a daily deletion rate from 504/2721 → 579/2874")
PY
)
printf '%s\n' "$FROZEN_OUT"
if ! printf '%s\n' "$FROZEN_OUT" | grep -q 'FAIL-TO-RECONCILE'; then
  echo "frozen_quote_probe: FAIL — expected non-reconciliation marker"
  FAIL=1
  OFFLINE_CORE_FAIL=1
else
  echo "frozen_quote_probe: PASS (embarrassment watched: non-reconciliation is the finding)"
fi
echo

# --- deletion-timer control: must be watchable RED ---
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
    OFFLINE_CORE_FAIL=1
  else
    echo "control_watched_red: PASS"
  fi
fi
echo

# --- anti-conflation ---
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
  OFFLINE_CORE_FAIL=1
fi
echo

# --- transcripto cannot answer file-age retention (honest product boundary) ---
echo "=== PRODUCT BOUNDARY (transcripto has no file-age retention command) ==="
set +e
HELP_OUT=$(transcripto --help 2>&1)
help_rc=$?
set -e
if printf '%s' "$HELP_OUT" | grep -Eiq 'retention|cleanupPeriod|older than|mtime'; then
  echo "product_boundary: FAIL — help mentions retention/mtime language"
  FAIL=1
  OFFLINE_CORE_FAIL=1
else
  echo "product_boundary: PASS — CLI help has no file-age retention verb"
fi
echo "help_exit: $help_rc"
echo

# --- stats near-miss: message counts can look like the retention denominator ---
echo "=== STATS NEAR-MISS (message counts ≠ file-age) ==="
if [ "$MODE" = "fixture" ]; then
  FAKE_HOME="$WORK/fake-home-stats"
  mkdir -p "$FAKE_HOME"
  set +e
  STATS_OUT=$(HOME="$FAKE_HOME" transcripto stats --root "$ROOT" 2>&1)
  stats_rc=$?
  set -e
  echo "stats_exit: $stats_rc"
  echo "stats_home: $FAKE_HOME (isolated; does not touch ~/.trace)"
  echo "stats_out:"
  printf '%s\n' "$STATS_OUT" | head -8
  # Detect the laundering risk: stats printing the retention denominator as a message count.
  if printf '%s\n' "$STATS_OUT" | grep -Eq '2,?721'; then
    echo "stats_near_miss: DETECTED — stats output contains 2721 (retention denominator lookalike)"
    echo "stats_near_miss_ruling: do NOT quote stats as retention evidence"
  else
    echo "stats_near_miss: no 2721 literal in stats output tonight"
  fi
  echo "stats_near_miss_probe: PASS (informational embarrassment hunt)"
else
  echo "stats_near_miss: skipped in live mode (do not index Oscar corpus here)"
fi
echo

# --- STEP 0 small-n gate ---
echo "=== STEP 0 · small-n gate ==="
set +e
STEP0_OUT=$(bash "$REPO_ROOT/scripts/test_small_n.sh" 2>&1)
step0rc=$?
set -e
printf '%s\n' "$STEP0_OUT"
if [ "$step0rc" -ne 0 ]; then
  echo "STEP 0: FAIL"
  FAIL=1
  OFFLINE_CORE_FAIL=1
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
  OFFLINE_CORE_FAIL=1
fi
echo

# --- privacy: real tree must pass; empty index must FAIL ---
# git archive extracts have no .git. Prior waves claimed stranger PASS on a
# clone only; archive mode was the bigger object and it failed. Ephemeral
# index over the extract makes privacy runnable without mutating a real repo.
echo "=== PRIVACY ==="
PRIVACY_SCAN_ROOT="$REPO_ROOT"
ARCHIVE_GIT_CLEANUP=""
if ! git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "privacy_mode: archive-extract (no .git) — ephemeral git add -A for scan"
  (
    cd "$REPO_ROOT"
    git init -q
    git add -A
  )
  ARCHIVE_GIT_CLEANUP="$REPO_ROOT/.git"
else
  echo "privacy_mode: git-worktree"
fi
set +e
PRIV_OUT=$(bash "$REPO_ROOT/test_privacy.sh" 2>&1)
privrc=$?
set -e
printf '%s\n' "$PRIV_OUT"
if [ "$privrc" -ne 0 ]; then
  echo "privacy on real tree: FAIL"
  FAIL=1
  OFFLINE_CORE_FAIL=1
else
  echo "privacy on real tree: PASS"
fi
if [ -n "$ARCHIVE_GIT_CLEANUP" ]; then
  rm -rf "$ARCHIVE_GIT_CLEANUP"
  echo "privacy_archive_ephemeral_git: removed"
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
) || { FAIL=1; OFFLINE_CORE_FAIL=1; }
echo

# --- regression suites ---
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
      OFFLINE_CORE_FAIL=1
    fi
  fi
done
echo

if [ "$OFFLINE_CORE_FAIL" -eq 0 ]; then
  echo "offline_core: PASS"
else
  echo "offline_core: FAIL"
fi
echo

# --- NETWORK PROBES (optional; SKIP ≠ PASS; restore proxies) ---
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY NO_PROXY
echo "=== NETWORK PROBES (optional; absence must not paint retention green) ==="
set +e
DOCS_MD=$(curl -fsSL --max-time 20 -A 'Mozilla/5.0' \
  https://code.claude.com/docs/en/settings-reference.md 2>/dev/null)
docs_rc=$?
set -e
if [ "$docs_rc" -eq 0 ] && [ -n "$DOCS_MD" ]; then
  echo "docs_object: https://code.claude.com/docs/en/settings-reference.md"
  # Write to a file then awk — `printf | awk` under pipefail dies with
  # "Broken pipe" when awk exits early on a large docs page (seen in CI).
  DOCS_FILE="$WORK/settings-reference.md"
  printf '%s\n' "$DOCS_MD" > "$DOCS_FILE"
  DEF=$(awk '
    /^### `cleanupPeriodDays`/ {insec=1; next}
    /^### / {if(insec) exit}
    insec && /^\* \*\*Default\*\*:/ {print; exit}
  ' "$DOCS_FILE")
  DDEF=$(awk '
    /^### `desktopSessionCleanupPeriodDays`/ {insec=1; next}
    /^### / {if(insec) exit}
    insec && /^\* \*\*Default\*\*:/ {print; exit}
  ' "$DOCS_FILE")
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
  echo "docs_object_fetch: SKIP (curl exit $docs_rc) — offline_core stands alone; do not carry a default from memory"
fi

set +e
PYPI_JSON=$(curl -fsSL --max-time 20 https://pypi.org/pypi/transcripto/json 2>/dev/null)
pypi_rc=$?
set -e
if [ "$pypi_rc" -eq 0 ] && [ -n "$PYPI_JSON" ]; then
  PYPI_VER=$(printf '%s' "$PYPI_JSON" | python -c "import json,sys; print(json.load(sys.stdin)['info']['version'])")
  echo "pypi_transcripto_version: $PYPI_VER (re-derived)"
else
  echo "pypi_object_fetch: SKIP (curl exit $pypi_rc)"
fi
echo

if [ "$FAIL" -eq 0 ]; then
  echo "cold_verify: PASS"
  exit 0
else
  echo "cold_verify: FAIL"
  exit 1
fi
