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
pat='/Users/morkeeth|-Users-morkeeth|omorke|beloeved routine|mTERMINAL 8|0d98a2c7|Obsidian LIFE|~/…/'
# The vault uses a numbered-folder convention. Match the CONVENTION, not a list of folder
# names: a folder-name list caught 5 of 11 real paths on 2026-09-04 and missed every one
# under "01 Projects/Job Hunt" and "02 Content". This pattern catches 11 of 11.
vault='(^|[^0-9])[0-9]{2} [A-Z][A-Za-z ]*/[^"]*\.md'
hits=$(git ls-files | grep -v -E '^test_privacy\.sh$' | xargs grep -n -i -E "$pat|$vault" 2>/dev/null)
if [ -n "$hits" ]; then echo "PRIVACY FAIL:"; echo "$hits" | head -20; exit 1; fi
echo "PRIVACY OK: 0 hits in $(git ls-files | wc -l | tr -d ' ') tracked files"
