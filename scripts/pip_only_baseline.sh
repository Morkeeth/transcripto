#!/usr/bin/env bash
# pip_only_baseline.sh — naive / pip-install-only arms vs transcripto source.
#
# Arm A (retention): naive `find` vs pip-installed transcripto.
# Arm B (authorship): naive type:user count vs pip-installed coach gate.
#
# Honest if naive wins. Requires network once for PyPI.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d /tmp/transcripto-pip-only-XXXXXX)"
FAIL=0

cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

echo "=== PIP-ONLY BASELINE · $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "repo: $REPO_ROOT"
echo "work: $WORK"
echo "note: this arm installs from PyPI; it is NOT a measure of transcripto source in this arm"
echo

python3 -m venv "$WORK/venv"
# shellcheck disable=SC1091
source "$WORK/venv/bin/activate"
python -m pip install -U pip -q
python -m pip install --no-cache-dir 'transcripto==0.2.0' -q
echo "pip_only_version: $(transcripto --version)"
# Prove we are not importing the repo tree.
cd "$WORK"
python - <<'PY'
import transcripto, os
p = os.path.realpath(transcripto.__file__)
print("transcripto.__file__:", p)
if "/workspace" in p or (p.endswith("transcripto.py") and "site-packages" not in p):
    raise SystemExit("FAIL: imported workspace/source tree instead of site-packages")
print("import_source: site-packages OK")
PY
echo

# --- Arm A: retention ---
echo "=== ARM A · retention (file ages) ==="
ROOT="$WORK/fixtures-retention-504-of-2721"
mkdir -p "$ROOT/demo-project/sessions"
FIXTURE_ROOT="$ROOT" python - <<'PY'
import os, time
from pathlib import Path
root = Path(os.environ["FIXTURE_ROOT"]) / "demo-project" / "sessions"
root.mkdir(parents=True, exist_ok=True)
now = time.time()
body = b'{"type":"user","promptSource":"typed","message":{"role":"user","content":"fixture turn"}}\n'
for i in range(2721):
    p = root / ("session-%04d.jsonl" % i)
    p.write_bytes(body)
    if i < 504:
        days = 31 + (i % 14)
        ts = now - days * 86400
        os.utime(p, (ts, ts))
print("fixture_files_written: 2721")
PY
THIRTY=$(date -d '30 days ago' +%Y-%m-%d)
FIND_TOTAL=$(find "$ROOT" -type f -name '*.jsonl' | wc -l | tr -d ' ')
FIND_OLD=$(find "$ROOT" -type f -name '*.jsonl' ! -newermt "$THIRTY" | wc -l | tr -d ' ')
echo "naive_find_ratio: $FIND_OLD of $FIND_TOTAL (threshold $THIRTY; -type f)"

set +e
HELP=$(transcripto --help 2>&1)
printf '%s\n' "$HELP" | grep -Eiq 'retention|cleanupPeriod|older than|mtime'
help_has_retention=$?
transcripto retention 2>"$WORK/ret.err" >/dev/null
ret_rc=$?
FAKE_HOME="$WORK/fake-home"
mkdir -p "$FAKE_HOME"
HOME="$FAKE_HOME" transcripto stats --root "$ROOT" 2>"$WORK/stats.err" | tee "$WORK/stats.out" >/dev/null
stats_rc=$?
set -e
echo "help_mentions_file_age_exit0: $help_has_retention  (1 means no — expected)"
echo "transcripto_retention_exit: $ret_rc  (nonzero expected — no such command)"
echo "transcripto_stats_exit: $stats_rc"
echo "stats_out_head:"
head -5 "$WORK/stats.out" 2>/dev/null || true
if printf '%s\n' "$(cat "$WORK/stats.out")" | grep -Eq '2,?721'; then
  echo "stats_near_miss: DETECTED on pip-only arm"
fi
if [ "$FIND_OLD" = "504" ] && [ "$FIND_TOTAL" = "2721" ] && [ "$help_has_retention" -ne 0 ] && [ "$ret_rc" -ne 0 ]; then
  echo "arm_a_ruling: naive find WINS retention; pip-only transcripto cannot answer file-age"
else
  echo "arm_a_ruling: UNEXPECTED (find=$FIND_OLD/$FIND_TOTAL help_age=$help_has_retention ret_rc=$ret_rc)"
  FAIL=1
fi
echo

# --- Arm B: authorship on copied coach fixture ---
echo "=== ARM B · authorship (pip-only coach vs naive) ==="
cp -R "$REPO_ROOT/fixtures-coach" "$WORK/fixtures-coach"
read -r NAIVE TOTAL <<EOF
$(python - <<PY
import json
from pathlib import Path
n=t=0
for line in Path("$WORK/fixtures-coach/coach-fixture.jsonl").read_text().splitlines():
    if not line.strip():
        continue
    t += 1
    if json.loads(line).get("type")=="user":
        n += 1
print(n, t)
PY
)
EOF
GATE_JSON=$(transcripto coach --root "$WORK/fixtures-coach" --json)
GATE=$(printf '%s' "$GATE_JSON" | python -c "import json,sys; print(json.load(sys.stdin)['human_turns'])")
echo "naive_type_user: $NAIVE"
echo "pip_only_human_turns: $GATE"
if [ "$NAIVE" -gt "$GATE" ]; then
  echo "arm_b_ruling: naive wins simplicity; pip-only gate is stricter ($GATE < $NAIVE) — expected"
else
  echo "arm_b_ruling: UNEXPECTED naive=$NAIVE gate=$GATE"
  FAIL=1
fi
echo

if [ "$FAIL" -eq 0 ]; then
  echo "pip_only_baseline: PASS"
  exit 0
else
  echo "pip_only_baseline: FAIL"
  exit 1
fi
