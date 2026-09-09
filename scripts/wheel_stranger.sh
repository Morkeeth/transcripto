#!/usr/bin/env bash
# wheel_stranger.sh — cold retention method from a local wheel (no editable, no .git).
#
# Bigger packaging object than `pip install -e .` inside a clone: build a wheel,
# install it offline into a fresh venv, then re-derive 504/2721 via find and prove
# the installed CLI still has no file-age retention verb.
#
# Embarrassing trap (found 2026-09-09): with cwd == the source checkout, Python
# puts '' first on sys.path and `import transcripto` silently binds the TREE,
# not the wheel — even after a successful `pip install`. pip_only_baseline
# avoided this by `cd` away from the repo; this script watches the trap go RED
# then re-proves the wheel from a clean cwd.
#
# Usage: bash scripts/wheel_stranger.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d /tmp/transcripto-wheel-stranger-XXXXXX)"
WHEEL_DIR="$WORK/wheels"
VENV="$WORK/venv"
EXTRACT="$WORK/extract"
FAIL=0

cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

echo "=== WHEEL STRANGER · $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "source_repo: $REPO_ROOT"
echo "work: $WORK"
echo

# Build wheel from source (may need network once for pip/build tooling).
python3 -m venv "$WORK/build-venv"
# shellcheck disable=SC1091
source "$WORK/build-venv/bin/activate"
python -m pip install -U pip -q
python -m pip wheel --no-deps "$REPO_ROOT" --wheel-dir "$WHEEL_DIR" -q
deactivate
WHEEL=$(ls "$WHEEL_DIR"/transcripto-*.whl | head -1)
echo "wheel: $WHEEL"
echo

# Archive extract proves packaging is not leaning on a live .git worktree.
git -C "$REPO_ROOT" archive --format=tar.gz -o "$WORK/src.tar.gz" HEAD
mkdir -p "$EXTRACT"
tar -xzf "$WORK/src.tar.gz" -C "$EXTRACT"
if [ -e "$EXTRACT/.git" ]; then
  echo "wheel_stranger: FAIL — extract contains .git"
  exit 1
fi
echo "archive_has_git: no"

# Fresh venv: install wheel ONLY (offline after wheel exists).
python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
export HTTP_PROXY=http://127.0.0.1:9
export HTTPS_PROXY=http://127.0.0.1:9
export ALL_PROXY=http://127.0.0.1:9
export NO_PROXY=
python -m pip install --no-index --find-links="$WHEEL_DIR" transcripto -q
echo "wheel_install: $(transcripto --version)"
echo

# --- CWD SHADOW TRAP: must be watched from inside the source checkout ---
echo "=== CWD SHADOW TRAP (source checkout on sys.path[0]) ==="
cd "$REPO_ROOT"
SHADOW=$(python - <<'PY'
import os, transcripto
p = os.path.realpath(transcripto.__file__)
print(p)
if "site-packages" in p:
    raise SystemExit("unexpected: cwd shadow did not bind the tree")
PY
)
echo "import_from_repo_cwd: $SHADOW"
if printf '%s' "$SHADOW" | grep -q "$REPO_ROOT"; then
  echo "cwd_shadow_trap: DETECTED — import transcripto from repo cwd binds the TREE, not the wheel"
  echo "cwd_shadow_trap_ruling: never verify a wheel install while cwd is the source checkout"
else
  echo "cwd_shadow_trap: FAIL — expected tree bind from repo cwd"
  FAIL=1
fi
echo

# --- Prove the wheel from a clean cwd (the real packaging object) ---
echo "=== WHEEL IMPORT FROM CLEAN CWD ==="
cd "$WORK"
python - <<'PY'
import os, transcripto
p = os.path.realpath(transcripto.__file__)
print("transcripto.__file__:", p)
if "site-packages" not in p:
    raise SystemExit("FAIL: expected site-packages import path, got " + p)
print("import_source: wheel site-packages OK")
PY
echo

# Retention method at the file object (same arithmetic fixture as cold_verify).
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
print("fixture_files_written: 2721 old_planted: 504")
PY
THIRTY=$(date -d '30 days ago' +%Y-%m-%d)
FORTYFIVE=$(date -d '45 days ago' +%Y-%m-%d)
TOTAL=$(find "$ROOT" -name '*.jsonl' | wc -l | tr -d ' ')
OLD30=$(find "$ROOT" -name '*.jsonl' ! -newermt "$THIRTY" | wc -l | tr -d ' ')
OLD45=$(find "$ROOT" -name '*.jsonl' ! -newermt "$FORTYFIVE" | wc -l | tr -d ' ')
echo "threshold_30d: $THIRTY"
echo "ratio_30d: $OLD30 of $TOTAL"
echo "older_than_45d: $OLD45"
if [ "$TOTAL" = "2721" ] && [ "$OLD30" = "504" ] && [ "$OLD45" = "0" ]; then
  echo "ASSERT fixture 504 of 2721 (old45=0): PASS"
else
  echo "ASSERT fixture 504 of 2721 (old45=0): FAIL (got $OLD30 of $TOTAL, old45=$OLD45)"
  FAIL=1
fi

# Product boundary on the WHEEL install from clean cwd.
set +e
HELP=$(transcripto --help 2>&1)
printf '%s\n' "$HELP" | grep -Eiq 'retention|cleanupPeriod|older than|mtime'
help_rc=$?
transcripto retention >/dev/null 2>&1
ret_rc=$?
set -e
echo "help_mentions_file_age_exit0: $help_rc  (1 means no — expected)"
echo "transcripto_retention_exit: $ret_rc  (nonzero expected)"
if [ "$help_rc" -eq 0 ] || [ "$ret_rc" -eq 0 ]; then
  echo "product_boundary_wheel: FAIL"
  FAIL=1
else
  echo "product_boundary_wheel: PASS"
fi

# Stats near-miss on wheel install + retention fixture.
FAKE_HOME="$WORK/fake-home"
mkdir -p "$FAKE_HOME"
set +e
STATS_OUT=$(HOME="$FAKE_HOME" transcripto stats --root "$ROOT" 2>&1)
stats_rc=$?
set -e
echo "stats_exit: $stats_rc"
echo "stats_out_head:"
printf '%s\n' "$STATS_OUT" | head -3
if printf '%s\n' "$STATS_OUT" | grep -Eq '2,?721'; then
  echo "stats_near_miss: DETECTED on wheel arm — do not quote as retention"
else
  echo "stats_near_miss: no 2721 literal on wheel arm tonight"
fi

# Prove PYTHONPATH is not the archive extract either.
python - <<PY
import os, transcripto
p = os.path.realpath(transcripto.__file__)
extract = os.path.realpath("$EXTRACT")
if p.startswith(extract + os.sep):
    raise SystemExit("FAIL: imported archive extract sources")
print("not_importing_archive_extract: PASS")
PY

if [ "$FAIL" -eq 0 ]; then
  echo "wheel_stranger: PASS"
  exit 0
else
  echo "wheel_stranger: FAIL"
  exit 1
fi
