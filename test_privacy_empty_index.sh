#!/usr/bin/env bash
# test_privacy_empty_index.sh — the empty-index green-on-outage trap must stay RED.
#
# Main's former test_privacy.sh printed "PRIVACY OK: 0 hits in 0 tracked files"
# and exited 0 on a fresh git init. That is not a clean tree.
set -euo pipefail
cd "$(dirname "$0")"
WORK=$(mktemp -d /tmp/transcripto-privacy-empty-XXXXXX)
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

(
  cd "$WORK"
  git init -q
  cp "$OLDPWD/test_privacy.sh" .
  set +e
  OUT=$(bash test_privacy.sh 2>&1)
  rc=$?
  set -e
  printf '%s\n' "$OUT"
  echo "privacy_empty_index_exit: $rc"
  if [ "$rc" -eq 0 ]; then
    echo "FAIL: privacy green on empty git index"
    exit 1
  fi
  echo "privacy_empty_index_watched_red: PASS"
)
