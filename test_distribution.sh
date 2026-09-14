#!/usr/bin/env bash
# Build the sdist, build a wheel FROM that archive, and test the installed CLI.
# Requires development-only `build`; installation below never uses an index.
set -euo pipefail
repo=$(cd -- "$(dirname -- "$0")" && pwd)
tmp=$(mktemp -d "${TMPDIR:-/tmp}/transcripto-dist.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
python3 -m build --outdir "$tmp/dist" "$repo"
python3 -m venv "$tmp/venv"
"$tmp/venv/bin/python" -m pip install --no-index --no-deps "$tmp"/dist/*.whl
TRANSCRIPTO_TEST_CLI="$tmp/venv/bin/transcripto" python3 -m unittest discover -s "$repo/tests" -p test_public_flow.py -v
