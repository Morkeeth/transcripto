#!/usr/bin/env bash
# Privacy guard: the public tree must carry none of the author's prompts, home paths,
# private ids, or personal-vault paths.
#
# WHAT THIS COVERS: literal home paths (both slash and dash-encoded forms), the author's
# email local-part, two known verbatim prompt fragments, one private id, and any reference
# to the personal Obsidian vault INCLUDING the elided "~/…/" form that hides the home path.
#
# WHAT THIS DOES NOT COVER, and you must not read a pass as "clean":
#   - author prompts other than the two literals below. There is no general detector.
#   - real repo names and real dated file traces, which ship on purpose as sample output.
#   - anything in a release already published. This reads the WORKING TREE only.
# The GitHub handle in repo URLs is public by definition and is allowed.
set -u
cd "$(dirname "$0")"
# Empty-index trap: `git ls-files` on a fresh `git init` is empty. A prior form of
# this guard printed "PRIVACY OK: 0 hits in 0 tracked files" and exited 0 — the
# green-on-outage failure mode. Fail closed when nothing is tracked.
n=$(git ls-files | wc -l | tr -d ' ')
if [ "$n" -eq 0 ]; then
  echo "PRIVACY FAIL: git ls-files returned 0 files (empty index is not a clean tree)"
  exit 1
fi
pat='/Users/morkeeth|-Users-morkeeth|omorke|beloeved routine|mTERMINAL 8|0d98a2c7|Obsidian LIFE|~/…/'
# The author's notes use a numbered-folder convention. Match the CONVENTION, not a list
# of folder names. A hand-written list of folder names caught 5 of 11 real paths on
# 2026-09-04 and missed 6, because the list only held the folders someone had thought of.
# The convention catches 11 of 11, including folders nobody has created yet. Do not
# replace this with a list, and do not name real folders in this file: the guard is
# public and a list of what you are hiding is itself a disclosure.
vault='(^|[^0-9])[0-9]{2} [A-Z][A-Za-z ]*/[^"]*\.md'
hits=$(git ls-files | grep -v -E '^test_privacy\.sh$' | xargs grep -n -i -E "$pat|$vault" 2>/dev/null)
if [ -n "$hits" ]; then echo "PRIVACY FAIL:"; echo "$hits" | head -20; exit 1; fi
echo "PRIVACY OK: 0 hits in $n tracked files"
