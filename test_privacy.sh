#!/usr/bin/env bash
# Privacy guard: production code and docs must carry no personal home paths,
# credential material, or numbered personal-note paths.
#
# Synthetic transcript fixtures intentionally use invented absolute paths and ids. They
# are tested as parser inputs elsewhere, so the path scan excludes fixture trees.
# Credential patterns still scan every tracked file, including fixtures.
#
# WHAT THIS DOES NOT COVER, and you must not read a pass as "clean":
#   - arbitrary personal prose. There is no general detector.
#   - anything deliberately encoded or encrypted.
#   - anything in a release already published. This reads the WORKING TREE only.
set -u
cd "$(dirname "$0")"
home='/(Users|home)/[^/[:space:]"]+/'
vault='(^|[^0-9])[0-9]{2} [A-Z][A-Za-z ]*/[^"]*\.md'
secret='AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9_]{20,}|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY'
files=$(git ls-files | grep -v -E '^(fixtures[^/]*/|fixtures/|test_privacy\.sh$)')
path_hits=$(printf '%s\n' "$files" | xargs grep -n -i -E "$home|$vault" 2>/dev/null)
secret_hits=$(git ls-files -z | xargs -0 grep -n -i -E "$secret" 2>/dev/null)
hits="$path_hits$secret_hits"
if [ -n "$hits" ]; then echo "PRIVACY FAIL:"; echo "$hits" | head -20; exit 1; fi
echo "PRIVACY OK: 0 structural hits in $(printf '%s\n' "$files" | wc -l | tr -d ' ') production/doc files; credential patterns checked across the tracked tree"
