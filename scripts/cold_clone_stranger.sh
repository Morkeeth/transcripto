#!/usr/bin/env bash
# cold_clone_stranger.sh — bigger object than "run in the agent worktree".
#
# Clones this branch into a disposable directory outside /workspace, then runs
# cold_verify from that clone. Proves the one-command stranger path does not
# depend on agent-home state, editable installs already on PATH, or uncommitted
# worktree dirt the clone would not see.
#
# Usage: bash scripts/cold_clone_stranger.sh
# Optional: TRANSCRIPTO_CLONE_REF=branch-or-sha (default: HEAD of this repo)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REF="${TRANSCRIPTO_CLONE_REF:-$(git -C "$REPO_ROOT" rev-parse HEAD)}"
WORK="$(mktemp -d /tmp/transcripto-cold-clone-XXXXXX)"
CLONE="$WORK/transcripto"

cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

echo "=== COLD CLONE STRANGER · $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "source_repo: $REPO_ROOT"
echo "ref: $REF"
echo "clone: $CLONE"
echo

# Local file:// clone — no GitHub network required once the agent has the ref.
git clone --quiet --no-checkout "file://$REPO_ROOT" "$CLONE"
git -C "$CLONE" checkout --quiet "$REF"
if [ ! -x "$CLONE/scripts/cold_verify.sh" ]; then
  echo "cold_clone_stranger: FAIL — clone missing scripts/cold_verify.sh at $REF"
  exit 1
fi
# Bigger-object guard: clone must not be the agent worktree.
CLONE_REAL=$(cd "$CLONE" && pwd -P)
REPO_REAL=$(cd "$REPO_ROOT" && pwd -P)
if [ "$CLONE_REAL" = "$REPO_REAL" ]; then
  echo "cold_clone_stranger: FAIL — clone path equals source worktree"
  exit 1
fi
echo "clone_ne_worktree: PASS ($CLONE_REAL ≠ $REPO_REAL)"
echo "running cold_verify inside clone…"
echo
TRANSCRIPTO_COLD_DIR="$WORK/cold" bash "$CLONE/scripts/cold_verify.sh"
