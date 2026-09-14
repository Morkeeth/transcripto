# Review return: Transcripto PR5 (receiving handoff + offline quickstart)

Lane: claude-review. Worktree: this branch only. Reviewed head: 1ab67351a3304bb31e6b3b2d4e882cfbc9b5e62d (PR #5 head, base aa4a392).
Fix commit: 3f25972f14df2c176a0ea284a35d16c0028701e5. Nothing pushed, merged, deployed or uploaded.

## Verdict

Safe to integrate at 3f25972f14df2c176a0ea284a35d16c0028701e5. Not safe at 1ab6735 (one provenance blocker, two shell-safety defects, eight traceback shapes).

## Evidence method

Wheel built with python -m build, installed with pip --no-index into a disposable venv, every probe run from /tmp with HOME set to a fresh temp directory (one of them named "home 3 it's $x"). No real ~/.claude, ~/.codex, ~/.cursor or ~/.transcripto data was read; ~/.transcripto/imports has no lab files after the run. Unsafe generated commands were never executed: the WHEEL= line was asserted by running only the assignment plus printf in sh inside a scratch directory and checking that a "$(touch marker)" embedded in the path created nothing.

## Defects found at 1ab6735 and fixed

| # | Defect | Probe at 1ab6735 | Fix |
|---|---|---|---|
| 1 | BLOCKER. Swapped source: cited line holds a different request, brief showed that request's outcomes as "Recorded follow-up". | Brief line: `- shell rm -rf /prod (unknown)` for a packet about the forecast cache. | Live events only when the normalised prompt equals the packet correction; otherwise packet record, titled "provisional, copied from the packet". Substring match replaced by equality so a short correction cannot match any prompt. |
| 2 | quickstart --wheel interpolated unquoted into WHEEL=. | `WHEEL=/tmp/.../it's a "dir" $(touch ...) ; echo hi/...whl`; sh roundtrip failed with unmatched quote. | shlex.quote on the assignment; sh roundtrip returns the exact path, no side effect. |
| 3 | Card exported HOME globally (constant and docs). | Line 12 `export HOME="$(mktemp -d)"`. | FLIGHT_HOME variable, each lab command prefixed `HOME="$FLIGHT_HOME"`. Doc regenerated from the constant; test asserts they match and neither exports HOME. |
| 4 | Wheel path with terminal escape printed raw. | od shows ESC ] 0 ; evil BEL in stdout. | Refuse with exit 2. |
| 5 | Citation path with terminal escape reached the Open: line. | brief Open: contained raw ESC. | safe_text guard, no Open line. |
| 6 | Tracebacks on malformed packets: citation string/list, source int, top-level list, recorded_follow_up string/dict/non-dict items (missing-source path), missing list with non-strings. | 8 shapes, rc=1 with Traceback. | _packet_error validates shape, exit 2 with one line. |
| 7 | missing: "abc" rendered as three bullets a, b, c. | Brief tail showed `- a - b - c`. | Covered by 6. |
| 8 | Brief labelled a live synthetic source as "source transcript" when the packet flag was absent. | Provenance line at pk_synthetic_str. | Packet flag OR live episode synthetic flag. |
| 9 | chmod 000 source reported "request match is uncertain". | Wording only. | Distinct "could not be read" state. |

## Verified working at 1ab6735 (unchanged)

- import-lab from installed wheel in a clean home: three labelled files, mode 0600, second run idempotent, edited file refused without --force.
- ask "retry" prints three Open: lines, shlex-quoted, correct for a HOME containing spaces, an apostrophe and a dollar sign. Each opens with --json to claude failed, codex succeeded, cursor unknown, synthetic true.
- replay --line on an absolute path works with a foreign HOME, so step 3 of the card needs no HOME prefix.
- Corrupted cited line, empty file, missing file each degrade to provisional without crash.

## Tests

- Unit suite: 94 tests pass (python3 -m unittest discover -s tests).
- test_distribution.sh: 15 public-flow tests pass against the installed wheel, including six new ReceivingAgentSafetyTests.
- CI matrix is 3.9 and 3.13; new code uses no 3.10+ syntax.

## Not done

- No push. No PR comment. Oscar integrates.
- Not verified on Python 3.9 locally (3.12 here); CI covers it.
