#!/usr/bin/env bash
# The version lives in two files and they drift silently. On 2026-08-31 the README
# documented 0.1.2 while PyPI served 0.1.1, so `uvx transcripto` gave a build without
# the commands the landing page advertised. That was found by hand, hours before a
# launch. This is the check that finds it instead.
cd "$(dirname "$0")"
PY=$(grep -oE 'VERSION = "[0-9.]+"' transcripto.py | head -1 | grep -oE '[0-9.]+')
TOML=$(grep -oE '^version = "[0-9.]+"' pyproject.toml | grep -oE '[0-9.]+')
FAIL=0
if [ "$PY" != "$TOML" ]; then
  echo "  FAIL  transcripto.py VERSION=$PY but pyproject.toml version=$TOML"; FAIL=1
else
  echo "  ok    version $PY matches in transcripto.py and pyproject.toml"
fi
# Installation pins must fail rather than merely warn: those commands are what
# a new reader will run. Other version mentions may be historical notes.
for pin in $(grep -oE 'transcripto==[0-9]+\.[0-9]+\.[0-9]+' README.md | sort -u); do
  if [ "$pin" != "transcripto==$PY" ]; then
    echo "  FAIL  README installs $pin, shipping $PY"; FAIL=1
  fi
done
# The README sells commands. If it names a version, it has to be this one.
# The old pattern was 'transcripto --version.*|[0-9]+\.[0-9]+\.[0-9]+'. The first alternative
# swallowed the whole line, and the ^-anchored second grep then discarded it. The version
# callout line is exactly where a version matters most, and it was the one line invisible to
# the check. Match version numbers only.
for v in $(grep -oE '[0-9]+\.[0-9]+\.[0-9]+' README.md | sort -u); do
  if [ "$v" != "$PY" ]; then
    echo "  WARN  README mentions $v, shipping $PY (fine if it is a changelog note, not fine if it is the install instruction)"
  fi
done
# The newest CHANGELOG heading is the release being shipped. A release whose notes
# still head with the previous version ships without its notes.
HEAD_CHANGE=$(grep -m1 -oE '^## [0-9]+\.[0-9]+\.[0-9]+' CHANGELOG.md | grep -oE '[0-9.]+')
if [ "$HEAD_CHANGE" != "$PY" ]; then
  echo "  FAIL  CHANGELOG.md newest entry is $HEAD_CHANGE, shipping $PY"; FAIL=1
else
  echo "  ok    CHANGELOG.md newest entry is $PY"
fi
[ "$FAIL" -eq 0 ] && echo "green." || { echo "1 RED."; exit 1; }
