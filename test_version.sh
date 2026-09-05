#!/usr/bin/env bash
# The version lives in two files and they drift silently. On 2026-08-31 the README
# documented 0.1.2 while PyPI served 0.1.1, so `uvx transcripto` gave a build without
# the commands the landing page advertised. That was found by hand, hours before a
# launch. This is the check that finds it instead.
#
# Install pins (`transcripto==X.Y.Z`) and `should print **X.Y.Z**` must match VERSION.
# Other README version mentions stay WARN (changelog / history notes).
cd "$(dirname "$0")"
PY=$(grep -oE 'VERSION = "[0-9.]+"' transcripto.py | head -1 | grep -oE '[0-9.]+')
TOML=$(grep -oE '^version = "[0-9.]+"' pyproject.toml | grep -oE '[0-9.]+')
FAIL=0
if [ "$PY" != "$TOML" ]; then
  echo "  FAIL  transcripto.py VERSION=$PY but pyproject.toml version=$TOML"; FAIL=1
else
  echo "  ok    version $PY matches in transcripto.py and pyproject.toml"
fi
# Hard-fail install pins and "should print" lines — these are what a stranger runs.
while IFS= read -r pin; do
  if [ -n "$pin" ] && [ "$pin" != "$PY" ]; then
    echo "  FAIL  README install pin transcripto==$pin but shipping $PY"
    FAIL=1
  fi
done < <(grep -oE 'transcripto==[0-9]+\.[0-9]+\.[0-9]+' README.md | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | sort -u)
while IFS= read -r sell; do
  if [ -n "$sell" ] && [ "$sell" != "$PY" ]; then
    echo "  FAIL  README says should print **$sell** but shipping $PY"
    FAIL=1
  fi
done < <(grep -oE 'should print \*\*[0-9]+\.[0-9]+\.[0-9]+\*\*' README.md | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | sort -u)
# Other version mentions: warn only (changelog / history).
for v in $(grep -oE '[0-9]+\.[0-9]+\.[0-9]+' README.md | sort -u); do
  if [ "$v" != "$PY" ]; then
    echo "  WARN  README mentions $v, shipping $PY (fine if it is a changelog note, not fine if it is the install instruction)"
  fi
done
[ "$FAIL" -eq 0 ] && echo "green." || { echo "1 RED."; exit 1; }
