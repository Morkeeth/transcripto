#!/usr/bin/env bash
# cold_verify.sh — stranger one-command path for the retention METHOD.
#
# Object: file ages under a projects root. NOT authorship / human_turns.
#   find "$ROOT" -type f -name '*.jsonl' | wc -l
#   find "$ROOT" -type f -name '*.jsonl' ! -newermt <30d> | wc -l
#
# Oscar's frozen quote (2026-08-28): 504 of 2,721 files older than 30 days.
# This VM usually has no ~/.claude/projects. When live corpus is absent, we
# generate an arithmetic-faithful fixture (2721 files, 504 aged 31–44d so
# older_than_45d stays 0) and assert exact counts. Live Oscar numbers are NOT
# re-derived here — they remain a machine-local quote.
#
# Ambition beyond planter/assert (tonight 2026-09-17):
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
#  11. DEATH-RATE IMPOSSIBILITY — refuse laundering +75 old / +153 total as deaths.
#  12. EMPTY-GREP + EMPTY-GREP -qv controls (outage must not read clean).
#  13. SYMLINK INFLATION — find without -type f double-counts; retention uses -type f.
#  14. HEAD archive privacy — committed tree must pass the same guard as worktree.
#  15. STRANGER PRODUCT JOURNEY — import-example → ask → changes → handoff →
#      receive-handoff in an isolated HOME (tonight's main promise, not retention).
#  16. PYPI WHEEL AUDIT — published 0.2.0 wheel must not silently contain cold_verify
#      (pip-install-only cannot reproduce the stranger retention script).
#  17. ENSUREPIP OUTAGE — `python3 -m venv` without ensurepip must not look green;
#      fall back to `python3 -m virtualenv` or FAIL clearly.
#  18. PUBLISHED STATS CAVEAT GAP — live 0.2.0 wheel stats must be checked for
#      the tip's anti-conflation caveat; absence is an embarrassment finding.
#  19. PUBLISHED VERB GAP — live wheel must be checked for tip stranger verbs
#      (import-example / changes / handoff / receive-handoff / import-lab /
#      quickstart). Absence means README stranger flow needs source, not pip-only.
#  20. VENV GREEN-WITHOUT-PIP — record when stdlib venv exits 0 with python but
#      no pip (ensurepip missing). That is DETECTED embarrassment, not silent skip.
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
# Watch ensurepip outage: `python3 -m venv` can leave a broken tree and still
# exit 0-ish depending on distro. Refuse a missing bin/python; prefer
# virtualenv when stdlib ensurepip is absent.
create_venv() {
  local dest="$1"
  rm -rf "$dest"
  set +e
  python3 -m venv "$dest" >"$WORK/venv-stdlib.err" 2>&1
  stdlib_rc=$?
  set -e
  echo "venv_stdlib_exit: $stdlib_rc"
  if [ "$stdlib_rc" -eq 0 ] && [ -x "$dest/bin/python" ]; then
    # ensurepip must have seeded pip, or the tree is an outage painted green.
    if "$dest/bin/python" -c 'import pip' 2>/dev/null; then
      echo "venv_backend: stdlib-venv"
      echo "venv_green_without_pip: no"
      return 0
    fi
    # Tonight's host trap: exit 0, python works, pip absent.
    echo "venv_green_without_pip: DETECTED — stdlib venv exit 0 with python but no pip"
    echo "venv_stdlib_ensurepip: MISSING — bin/python exists but pip import fails"
    rm -rf "$dest"
  else
    echo "venv_green_without_pip: no (stdlib venv did not claim success)"
    echo "venv_stdlib: FAIL (exit $stdlib_rc) — see ensurepip / python3-venv"
    head -5 "$WORK/venv-stdlib.err" 2>/dev/null || true
    rm -rf "$dest"
  fi
  set +e
  if [ -x "$HOME/.local/bin/virtualenv" ]; then
    "$HOME/.local/bin/virtualenv" -p "$(command -v python3)" "$dest" >"$WORK/venv-virtualenv.err" 2>&1
    ve_rc=$?
  else
    python3 -m virtualenv "$dest" >"$WORK/venv-virtualenv.err" 2>&1
    ve_rc=$?
  fi
  set -e
  if [ "$ve_rc" -eq 0 ] && [ -x "$dest/bin/python" ] \
      && "$dest/bin/python" -c 'import pip' 2>/dev/null; then
    echo "venv_backend: virtualenv-fallback (ensurepip outage watched)"
    return 0
  fi
  echo "cold_verify: FAIL — cannot create usable venv (stdlib + virtualenv both failed)"
  cat "$WORK/venv-virtualenv.err" 2>/dev/null || true
  return 1
}

create_venv "$VENV" || exit 1
if [ ! -x "$VENV/bin/python" ]; then
  echo "cold_verify: FAIL — venv missing $VENV/bin/python"
  exit 1
fi
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
# Prove the venv can import pip after bootstrap (ensurepip outage must not look green).
python -c 'import pip,sys; print("venv_pip_ok:", pip.__version__, "py", sys.version.split()[0])'
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

if [ -d "$LIVE_ROOT" ] && find "$LIVE_ROOT" -type f -name '*.jsonl' -print -quit 2>/dev/null | grep -q .; then
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
# Always -type f: without it, symlinks inflate the total (trap watched below).
THIRTY=$(date -d '30 days ago' +%Y-%m-%d)
FORTYFIVE=$(date -d '45 days ago' +%Y-%m-%d)
TOTAL=$(find "$ROOT" -type f -name '*.jsonl' | wc -l | tr -d ' ')
OLD30=$(find "$ROOT" -type f -name '*.jsonl' ! -newermt "$THIRTY" | wc -l | tr -d ' ')
OLD45=$(find "$ROOT" -type f -name '*.jsonl' ! -newermt "$FORTYFIVE" | wc -l | tr -d ' ')

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
done < <(find "$ROOT" -type f -name '*.jsonl' -print0)

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

# --- DEATH-RATE IMPOSSIBILITY (two frozen stamps must not print deletions/day) ---
# Quotes only — do not treat these as live re-derives. The control refuses the
# laundering move: (579-504)=75 "deaths" while total rose 2721→2874 (+153).
echo "=== DEATH-RATE IMPOSSIBILITY (frozen stamps are quotes, not live) ==="
set +e
DEATH_RATE_REPORT=$(python - <<'PY'
# Frozen Oscar quotes (machine-local; not re-derived on this VM):
old_a, total_a = 504, 2721   # 2026-08-28
old_b, total_b = 579, 2874   # 2026-08-29
d_old = old_b - old_a
d_total = total_b - total_a
print("frozen_delta_old30: %+d" % d_old)
print("frozen_delta_total: %+d" % d_total)
deaths_if_naive = d_old  # the laundering figure someone might print
print("laundered_death_claim_if_printed: %d (FORBIDDEN)" % deaths_if_naive)
if d_total > 0 and d_old > 0:
    print("death_rate_impossible: PASS — total rose and old30 rose; refuse daily death rate")
    raise SystemExit(0)
if d_total >= 0 and deaths_if_naive > 0:
    print("death_rate_impossible: PASS — refuse to treat +old30 as deaths while total did not fall")
    raise SystemExit(0)
print("death_rate_impossible: FAIL — unexpected stamp relationship")
raise SystemExit(1)
PY
)
death_rc=$?
set -e
printf '%s\n' "$DEATH_RATE_REPORT"
if [ "$death_rc" -ne 0 ]; then
  FAIL=1
  OFFLINE_CORE_FAIL=1
fi
echo

# --- EMPTY-GREP controls (green-on-outage class) ---
# `printf '' | grep -q .` exits 1. `printf '' | grep -qv x` also exits 1.
# A check that treats "grep found nothing / inverted miss" as CLEAN without
# also proving the input stream was non-empty is the outage trap.
echo "=== EMPTY-GREP CONTROL (outage must not read clean) ==="
set +e
printf '' | grep -q .
empty_grep_rc=$?
printf '' | grep -qv 'x'
empty_grep_qv_rc=$?
set -e
echo "empty_input_grep_q_dot_exit: $empty_grep_rc  (expect 1)"
echo "empty_input_grep_qv_x_exit: $empty_grep_qv_rc  (expect 1 — prompt trap)"
if [ "$empty_grep_rc" -eq 0 ] || [ "$empty_grep_qv_rc" -eq 0 ]; then
  echo "empty_grep_control: FAIL — grep matched empty input (q=$empty_grep_rc qv=$empty_grep_qv_rc)"
  FAIL=1
  OFFLINE_CORE_FAIL=1
else
  echo "empty_grep_control: PASS — both -q and -qv exit 1 on empty; not CLEAN without a non-empty guard"
fi
echo

# --- SYMLINK INFLATION (find without -type f double-counts) ---
echo "=== SYMLINK INFLATION TRAP (omit -type f → inflated totals) ==="
SYM="$WORK/symlink-inflation"
mkdir -p "$SYM"
printf '%s\n' '{"k":1}' > "$SYM/real.jsonl"
ln -s "$SYM/real.jsonl" "$SYM/alias.jsonl"
SYM_NAME=$(find "$SYM" -name '*.jsonl' | wc -l | tr -d ' ')
SYM_TYPEF=$(find "$SYM" -type f -name '*.jsonl' | wc -l | tr -d ' ')
echo "symlink_find_name_only: $SYM_NAME"
echo "symlink_find_type_f: $SYM_TYPEF"
if [ "$SYM_NAME" = "2" ] && [ "$SYM_TYPEF" = "1" ]; then
  echo "symlink_inflation: DETECTED — name-only find counted 2; -type f counted 1"
  echo "symlink_inflation_ruling: retention method MUST use find -type f -name '*.jsonl'"
  echo "symlink_inflation_probe: PASS"
else
  echo "symlink_inflation: FAIL — expected name=2 type_f=1 (got name=$SYM_NAME type_f=$SYM_TYPEF)"
  FAIL=1
  OFFLINE_CORE_FAIL=1
fi
echo

# --- NEGATIVE PLANTER: wrong plant MUST fail the 504/2721 assert (watched RED) ---
echo "=== NEGATIVE PLANTER (must go RED — control that can fail) ==="
NEG_ROOT="$WORK/fixtures-retention-WRONG-503-of-2720"
plant_retention_fixture "$NEG_ROOT" 2720 503
NEG_TOTAL=$(find "$NEG_ROOT" -type f -name '*.jsonl' | wc -l | tr -d ' ')
NEG_OLD=$(find "$NEG_ROOT" -type f -name '*.jsonl' ! -newermt "$THIRTY" | wc -l | tr -d ' ')
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
rng = random.Random(20260917)  # reproducible tonight; not the retention quote
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
        ["bash", "-lc", f"find '{root}' -type f -name '*.jsonl' ! -newermt '{ymd}' | wc -l"],
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
print("(seed Random(20260917) — not the retention quote; collision guard active)")
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
  elif [ "$UTC_THIRTY" = "$TOKYO_THIRTY" ] && [ "$UTC_THIRTY" != "$LA_THIRTY" ]; then
    # Tonight 2026-09-11 ~00:14Z: UTC/Tokyo/London=2026-08-12, LA=2026-08-11.
    # The prior-wave trap (UTC↔LA agree, Tokyo differs) did not fire; the inverse did.
    echo "tz_pair_trap: DETECTED — UTC↔Tokyo agree ($UTC_THIRTY) while LA differs ($LA_THIRTY)"
    echo "tz_pair_trap_ruling: which pair you pick decides whether divergence looks absent"
  elif [ "$UTC_THIRTY" = "$LONDON_THIRTY" ] && [ "$UTC_THIRTY" != "$LA_THIRTY" ]; then
    echo "tz_pair_trap: DETECTED — UTC↔London agree ($UTC_THIRTY) while LA differs ($LA_THIRTY)"
    echo "tz_pair_trap_ruling: European pair can hide Pacific divergence"
  else
    echo "tz_pair_trap: mixed pattern tonight (UTC=$UTC_THIRTY LA=$LA_THIRTY Tokyo=$TOKYO_THIRTY London=$LONDON_THIRTY)"
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

# --- STRANGER PRODUCT JOURNEY (tonight's main — distinct from retention) ---
# Bigger object than "tests pass": drive the README stranger flow as the
# intended user in an isolated HOME, offline, with no agent dotfiles.
echo "=== STRANGER PRODUCT JOURNEY (import-example → ask → changes → handoff) ==="
JOURNEY_HOME="$WORK/stranger-home"
JOURNEY_OUT="$WORK/stranger-journey.out"
mkdir -p "$JOURNEY_HOME/codex-inbox" "$JOURNEY_HOME/codex-work"
set +e
(
  export HOME="$JOURNEY_HOME"
  transcripto import-example
  transcripto ask "What changed about the forecast cache?"
  transcripto changes
  transcripto handoff "30 seconds" \
    --to-harness codex --output "$HOME/codex-inbox/correction.json"
  transcripto receive-handoff \
    "$HOME/codex-inbox/correction.json" --as-harness codex \
    --output "$HOME/codex-work/receiver-brief.md"
  echo "--- brief head ---"
  head -40 "$HOME/codex-work/receiver-brief.md"
) >"$JOURNEY_OUT" 2>&1
journey_rc=$?
set -e
echo "stranger_journey_exit: $journey_rc"
echo "stranger_journey_home: $JOURNEY_HOME"
# Evidence at the object: ask hits, changes output, brief exists with Open: + statuses.
ASK_HITS=$(grep -c 'Open:' "$JOURNEY_OUT" || true)
BRIEF="$JOURNEY_HOME/codex-work/receiver-brief.md"
BRIEF_OK=0
if [ -f "$BRIEF" ]; then
  if grep -q 'Open:' "$BRIEF" && grep -Eiq 'failed|succeeded|unknown' "$BRIEF"; then
    BRIEF_OK=1
  fi
fi
HANDOFF_MODE="missing"
if [ -f "$JOURNEY_HOME/codex-inbox/correction.json" ]; then
  HANDOFF_MODE=$(stat -c '%a' "$JOURNEY_HOME/codex-inbox/correction.json")
fi
echo "stranger_ask_open_count: $ASK_HITS"
echo "stranger_brief_ok: $BRIEF_OK"
echo "stranger_handoff_mode: $HANDOFF_MODE"
tail -20 "$JOURNEY_OUT" | sed 's/^/  /'
if [ "$journey_rc" -eq 0 ] && [ "$ASK_HITS" -ge 1 ] && [ "$BRIEF_OK" -eq 1 ] && [ "$HANDOFF_MODE" = "600" ]; then
  echo "stranger_product_journey: PASS"
else
  echo "stranger_product_journey: FAIL (rc=$journey_rc ask_open=$ASK_HITS brief_ok=$BRIEF_OK mode=$HANDOFF_MODE)"
  FAIL=1
  OFFLINE_CORE_FAIL=1
fi
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
    if printf '%s\n' "$STATS_OUT" | grep -Fq 'not transcript file ages'; then
      echo "stats_anti_conflation_caveat: PASS — stats names the object (messages ≠ file ages)"
    else
      echo "stats_anti_conflation_caveat: FAIL — near-miss digit without object caveat"
      FAIL=1
      OFFLINE_CORE_FAIL=1
    fi
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
# HEAD vs worktree: privacy greps working-tree bytes of tracked paths. A staged
# scrub can pass while HEAD (and git archive) still leaks. Verify by extracting
# HEAD and running the same guard — without restating guarded fragments here.
if git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  HEAD_TREE="$WORK/privacy-head-extract"
  rm -rf "$HEAD_TREE"
  mkdir -p "$HEAD_TREE"
  git -C "$REPO_ROOT" archive HEAD | tar -x -C "$HEAD_TREE"
  (
    cd "$HEAD_TREE"
    git init -q
    git add -A
    set +e
    OUT=$(bash test_privacy.sh 2>&1)
    rc=$?
    set -e
    printf '%s\n' "$OUT"
    echo "privacy_HEAD_extract_exit: $rc"
    if [ "$rc" -ne 0 ]; then
      echo "privacy_HEAD_vs_worktree: FAIL — committed tree fails privacy (worktree scrub is not enough)"
      exit 1
    fi
    echo "privacy_HEAD_vs_worktree: PASS — git archive of HEAD is clean"
  ) || { FAIL=1; OFFLINE_CORE_FAIL=1; }
  rm -rf "$HEAD_TREE"
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
  # Bigger packaging object: does the published wheel ship cold_verify?
  # If it does not, "pip install transcripto" alone cannot reproduce the
  # stranger retention script — clone/archive is required.
  set +e
  WHEEL_URL=$(printf '%s' "$PYPI_JSON" | python -c "
import json,sys
files=json.load(sys.stdin)['urls']
wheels=[u for u in files if u.get('packagetype')=='bdist_wheel']
print(wheels[0]['url'] if wheels else '')
")
  set -e
  if [ -n "$WHEEL_URL" ]; then
    WHEEL_NAME=$(basename "$WHEEL_URL" | sed 's/[?#].*//')
    case "$WHEEL_NAME" in
      *.whl) ;;
      *) WHEEL_NAME="transcripto-from-pypi.whl" ;;
    esac
    WHEEL_TMP="$WORK/$WHEEL_NAME"
    set +e
    curl -fsSL --max-time 40 -o "$WHEEL_TMP" "$WHEEL_URL"
    wheel_dl=$?
    set -e
    if [ "$wheel_dl" -eq 0 ]; then
      COLD_IN_WHEEL=$(python - <<PY
import zipfile, sys
z=zipfile.ZipFile("$WHEEL_TMP")
names=z.namelist()
print(sum(1 for n in names if "cold_verify" in n))
print("wheel_file_count: %d" % len(names), file=sys.stderr)
PY
)
      echo "pypi_wheel_cold_verify_entries: $COLD_IN_WHEEL"
      echo "pypi_wheel_local_name: $WHEEL_NAME"
      if [ "$COLD_IN_WHEEL" = "0" ]; then
        echo "pypi_package_audit: PASS — published wheel has 0 cold_verify entries; pip-only cannot ship stranger retention"
      else
        echo "pypi_package_audit: NOTE — wheel unexpectedly contains cold_verify ($COLD_IN_WHEEL)"
      fi
      # Beyond-floor embarrassment: does published 0.2.0 stats name the object?
      # Tip adds an anti-conflation caveat; if the live wheel lacks it, quoting
      # pip-installed stats as retention proof is still a live footgun.
      echo
      echo "=== PUBLISHED STATS CAVEAT GAP (PyPI wheel vs tip) ==="
      PUB_VENV="$WORK/pypi-stats-venv"
      rm -rf "$PUB_VENV"
      # Must NOT use the activated cold_verify interpreter: it has no virtualenv
      # module, and stdlib venv on ensurepip-less images yields bin/python without pip.
      SYS_PY="${TRANSCRIPTO_SYSTEM_PYTHON:-/usr/bin/python3}"
      set +e
      if [ -x "$HOME/.local/bin/virtualenv" ]; then
        "$HOME/.local/bin/virtualenv" -p "$SYS_PY" "$PUB_VENV" >"$WORK/pypi-stats-venv.err" 2>&1
        pub_ve_rc=$?
      else
        env -u VIRTUAL_ENV "$SYS_PY" -m virtualenv "$PUB_VENV" >"$WORK/pypi-stats-venv.err" 2>&1
        pub_ve_rc=$?
      fi
      set -e
      if [ -x "$PUB_VENV/bin/python" ] && "$PUB_VENV/bin/python" -c 'import pip' 2>/dev/null; then
        set +e
        "$PUB_VENV/bin/python" -m pip install --no-index "$WHEEL_TMP" -q
        pub_install_rc=$?
        set -e
        if [ "$pub_install_rc" -ne 0 ]; then
          echo "published_stats_caveat: SKIP — wheel install into probe venv failed (rc=$pub_install_rc)"
        else
          PUB_HOME="$WORK/pypi-stats-home"
          mkdir -p "$PUB_HOME"
          PUB_ROOT="$ROOT"
          set +e
          PUB_STATS=$(cd "$WORK" && HOME="$PUB_HOME" "$PUB_VENV/bin/transcripto" stats --root "$PUB_ROOT" 2>&1)
          pub_stats_rc=$?
          set -e
          echo "published_stats_exit: $pub_stats_rc"
          echo "published_stats_head:"
          printf '%s\n' "$PUB_STATS" | head -4
          if printf '%s\n' "$PUB_STATS" | grep -Fq 'File retention is a find/mtime question'; then
            echo "published_stats_caveat: PRESENT — live wheel already names the object"
          else
            echo "published_stats_caveat: ABSENT — live $PYPI_VER wheel lacks tip anti-conflation caveat"
            echo "published_stats_caveat_ruling: embarrassment — pip-only stats can still look like retention"
            echo "published_stats_caveat_probe: PASS (gap watched; tip repair is this branch)"
          fi
          set +e
          TIP_STATS=$(HOME="$PUB_HOME" transcripto stats --root "$PUB_ROOT" 2>&1)
          set -e
          if printf '%s\n' "$TIP_STATS" | grep -Fq 'File retention is a find/mtime question'; then
            echo "tip_stats_caveat: PRESENT"
          else
            echo "tip_stats_caveat: FAIL — tip lost the anti-conflation caveat"
            FAIL=1
          fi
          # Beyond-floor (tonight): published wheel verb gap vs tip stranger flow.
          echo
          echo "=== PUBLISHED VERB GAP (PyPI wheel vs tip stranger flow) ==="
          VERB_REPORT=$(cd "$WORK" && "$PUB_VENV/bin/python" - <<'PY'
import inspect, re, sys
# Prefer the installed site-packages copy over a cwd-shadowed tree module.
import transcripto
mod_file = getattr(transcripto, "__file__", "") or ""
print("published_module_file: " + mod_file)
if "site-packages" not in mod_file.replace("\\", "/"):
    print("published_module_cwd_shadow: DETECTED — imported tree/non-wheel copy")
else:
    print("published_module_cwd_shadow: no")
src = inspect.getsource(transcripto)
parsers = re.findall(r'add_parser\("([\w-]+)"\)', src)
need = ["import-example", "changes", "handoff", "receive-handoff", "import-lab", "quickstart"]
missing = [n for n in need if n not in parsers]
print("published_parsers: " + ",".join(parsers))
print("published_stranger_verbs_missing: " + (",".join(missing) if missing else "(none)"))
if missing:
    print("published_verb_gap: DETECTED — pip-only missing " + ",".join(missing) + "; README stranger flow needs source/tip")
    print("published_verb_gap_probe: PASS (gap watched; not a cold_verify fail)")
else:
    print("published_verb_gap: none — live wheel has tip stranger verbs")
    print("published_verb_gap_probe: PASS")
PY
)
          printf '%s\n' "$VERB_REPORT"
          # Tip source verbs (open the tree file, not an import from cwd).
          set +e
          TIP_VERBS=$(python - <<PY
import re
from pathlib import Path
src = Path("$REPO_ROOT/transcripto.py").read_text()
parsers = re.findall(r'add_parser\("([\w-]+)"\)', src)
need = ["import-example", "changes", "handoff", "receive-handoff", "import-lab", "quickstart"]
missing = [n for n in need if n not in parsers]
print("tip_parsers_stranger: " + ",".join([n for n in need if n in parsers]))
print("tip_stranger_verbs_missing: " + (",".join(missing) if missing else "(none)"))
if missing:
    raise SystemExit("tip missing stranger verbs: " + ",".join(missing))
print("tip_stranger_verbs: PRESENT")
PY
)
          tip_verbs_rc=$?
          set -e
          printf '%s\n' "$TIP_VERBS"
          if [ "$tip_verbs_rc" -ne 0 ]; then
            echo "tip_stranger_verbs: FAIL"
            FAIL=1
          fi
        fi
      else
        echo "published_stats_caveat: SKIP — could not create probe venv with pip (rc=${pub_ve_rc:-?})"
        head -8 "$WORK/pypi-stats-venv.err" 2>/dev/null || true
      fi
    else
      echo "pypi_wheel_download: SKIP (curl exit $wheel_dl)"
    fi
  else
    echo "pypi_wheel_url: SKIP (no bdist_wheel in JSON)"
  fi
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
