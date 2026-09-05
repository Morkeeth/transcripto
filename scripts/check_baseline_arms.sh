#!/usr/bin/env bash
# Baseline arm: tip wheel vs live PyPI on the READ-CONTRACT schema-7 select.
# Tip must PASS. Published package must FAIL until a schema-7 release ships.
# This is the embarrassing comparison — not a CI gate (PyPI lag is expected).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

echo "=== ARM A: tip wheel ==="
bash "$ROOT/scripts/check_consumer_integration.sh" | tee "$WORKDIR/tip.txt"
tip_rc=${PIPESTATUS[0]}
echo "tip_exit=$tip_rc"

echo
echo "=== ARM B: live PyPI (clean-room cwd=/tmp) ==="
python3 -m venv "$WORKDIR/pypi"
# shellcheck disable=SC1091
source "$WORKDIR/pypi/bin/activate"
cd /tmp
pip install -q --upgrade pip
pip install -q --no-cache-dir 'transcripto==0.2.0'
EH="$WORKDIR/home-pypi"
mkdir -p "$EH"
set +e
HOME="$EH" transcripto index --root "$ROOT/fixtures-cursor" >/dev/null
HOME="$EH" python3 - <<'PY'
import os, sqlite3, sys
con = sqlite3.connect("file:%s?mode=ro" % os.path.expanduser("~/.trace/trace.db"), uri=True)
uv = con.execute("PRAGMA user_version").fetchone()[0]
print("pypi_user_version", uv)
try:
    con.execute("select session_file, source_line, record_sha256 from v_messages limit 1").fetchone()
    print("pypi_schema7_select PASS")
    sys.exit(0)
except Exception as e:
    print("pypi_schema7_select FAIL", type(e).__name__, e)
    sys.exit(1)
PY
pypi_rc=$?
set -e
echo "pypi_exit=$pypi_rc"

echo
if [ "$tip_rc" -eq 0 ] && [ "$pypi_rc" -ne 0 ]; then
  echo "BASELINE RESULT: tip wins consumer contract; live PyPI 0.2.0 loses (expected until publish)"
  exit 0
elif [ "$tip_rc" -eq 0 ] && [ "$pypi_rc" -eq 0 ]; then
  echo "BASELINE RESULT: both pass — collision may be resolved or check is wrong"
  exit 0
else
  echo "BASELINE RESULT: unexpected (tip_exit=$tip_rc pypi_exit=$pypi_rc)"
  exit 1
fi
