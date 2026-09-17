#!/usr/bin/env bash
# Wrapper so `bash scripts/test_small_n.sh` matches the START one-liner.
set -euo pipefail
cd "$(dirname "$0")/.."
exec bash ./test_small_n.sh
