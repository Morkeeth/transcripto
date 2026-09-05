#!/usr/bin/env bash
# Thin wrapper so the START one-liner `bash scripts/test_small_n.sh` works.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec bash "$ROOT/test_small_n.sh"
