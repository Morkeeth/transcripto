#!/usr/bin/env bash
# archive_stranger.sh — cold verify from a git-archive extract (no .git).
#
# Bigger object than "clone and run": strangers who download a tarball have
# no git index. Prior waves claimed stranger PASS after only testing a clone.
#
# Usage: bash scripts/archive_stranger.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d /tmp/transcripto-archive-stranger-XXXXXX)"
ARCHIVE="$WORK/transcripto.tar.gz"
EXTRACT="$WORK/extract"

cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

echo "=== ARCHIVE STRANGER · $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "source_repo: $REPO_ROOT"
echo "extract: $EXTRACT"
echo

git -C "$REPO_ROOT" archive --format=tar.gz -o "$ARCHIVE" HEAD
mkdir -p "$EXTRACT"
tar -xzf "$ARCHIVE" -C "$EXTRACT"
if [ -e "$EXTRACT/.git" ]; then
  echo "archive_stranger: FAIL — extract unexpectedly contains .git"
  exit 1
fi
echo "archive_has_git: no"
echo "running cold_verify inside extract…"
echo
bash "$EXTRACT/scripts/cold_verify.sh"
