# Cold verify — 2026-08-30 artifact (re-run 2026-09-09)

**One command (cold stranger, no key, no Oscar corpus):**

```sh
bash scripts/cold_verify.sh
```

**Archive stranger (no `.git`):**

```sh
bash scripts/archive_stranger.sh
```

**Wheel stranger (local wheel, offline install, clean cwd):**

```sh
bash scripts/wheel_stranger.sh
```

**Prerequisite on Debian/Ubuntu cloud images:** `python3-venv`
(`sudo apt install python3-venv`). Without it, `python3 -m venv` fails.

## What this verifies

The **file-age method** behind the retention story:

```sh
ROOT=~/.claude/projects   # or the generated fixture on a cloud VM
THIRTY=$(date -d '30 days ago' +%Y-%m-%d)
TOTAL=$(find "$ROOT" -name '*.jsonl' | wc -l)
OLD30=$(find "$ROOT" -name '*.jsonl' ! -newermt "$THIRTY" | wc -l)
echo "$OLD30 of $TOTAL older than 30d (as of $THIRTY)"
echo "TZ=$(date +%Z)"
```

**Object:** jsonl **files** under a projects root, aged by mtime.
**Not** an authorship-gate count of human turns. **Not** `stats` message counts.

Frozen Oscar quotes (machine-local; **not** re-derived on this VM):

| stamp | figure | note |
|-------|--------|------|
| 2026-08-28 | 504 of 2,721 | weekly review freeze |
| 2026-08-29 | 579 of 2,874 | same `find` method next day |

The two stamps do not reconcile by arithmetic. No daily death rate is claimed
from the delta. The sharper companion fact on Oscar's machine was
`older_than_45d == 0` — deletion already happened; it is not a future risk only.

When `~/.claude/projects` is absent, the script generates an
**arithmetic-faithful fixture**: 2721 files, 504 touched to ages 31–44 days
(so the 45-day count stays 0), and asserts exact equality. A **negative
planter** (503 of 2720) must fail that assert. An **independent oracle**
compares `find` to Python `st_mtime` on 180 blind ages that do not share the
504/2721 target (seed `20260909` tonight; collision with 504/2721 fails).

## Captured output

Command run tonight: `bash scripts/cold_verify.sh` (exit 0).

```text
=== COLD VERIFY · 2026-09-09T00:11:32Z ===
repo: /workspace
work: /tmp/transcripto-cold-tonight2

transcripto: transcripto 0.2.0

=== OFFLINE CORE (proxies poisoned to 127.0.0.1:9) ===

generating fixture: 2721 jsonl files (504 aged 31–44d)…
fixture_files_written: 2721 old_planted: 504
retention source: FIXTURE /tmp/transcripto-cold-tonight2/fixtures-retention-504-of-2721
  (no live ~/.claude/projects on this machine — method + arithmetic only)

=== RETENTION (find method, re-derived) ===
mode: fixture
as_of: 2026-09-09T00:11:38Z
threshold_30d: mtime <= 2026-08-10
threshold_45d: mtime <= 2026-07-26
total_jsonl: 2721
older_than_30d: 504
older_than_45d: 0
ratio_30d: 504 of 2721
oldest_file: /tmp/transcripto-cold-tonight2/fixtures-retention-504-of-2721/demo-project/sessions/session-0055.jsonl
oldest_mtime: 2026-07-27T00:11:35Z

frozen_quote (Oscar 2026-08-28, NOT re-derived on this VM unless mode=live): 504 of 2,721
frozen_rederive (Oscar 2026-08-29, NOT re-derived here): 579 of 2,874
NOTE: the two frozen stamps do not reconcile by arithmetic; no daily death rate is claimed.

ASSERT fixture 504 of 2721 (old45=0): PASS

=== NEGATIVE PLANTER (must go RED — control that can fail) ===
fixture_files_written: 2720 old_planted: 503
negative_plant: 503 of 2720 (deliberately not 504 of 2721)
negative_planter_assert_would_reject: YES (got 503 of 2720)
negative_planter: PASS — watched RED (wrong plant does not satisfy 504/2721)

=== INDEPENDENT ORACLE (find ↔ Python mtime, blind ages) ===
oracle_files: 180
oracle_age_days_min_max: 0 60
oracle_python_old30: 88
oracle_find_old30: 88
oracle_python_old45: 45
oracle_find_old45: 45
threshold_30d_epoch: 1786320000.0
threshold_45d_epoch: 1785024000.0
independent_oracle: PASS

=== BOUNDARY PROBE (exactly at threshold) ===
threshold_midnight_epoch: 1786320000 (2026-08-10 00:00:00 local)
counted_by_bang_newermt at_midnight: 1   (expect 1 — mtime == ref is NOT newer)
counted_by_bang_newermt one_sec_after: 0   (expect 0 — strictly newer)
counted_by_bang_newermt one_sec_before: 1   (expect 1)
boundary_probe: PASS — ! -newermt means mtime <= threshold midnight
duration_vs_calendar: file aged exactly 30*86400s counted_by_bang_newermt=0
  (0 means calendar method is stricter than pure duration at this clock time;
   1 means the duration-aged file already sits on/before threshold midnight)
caveat: article find method uses calendar midnight, not age_seconds > 30*86400

=== TZ DIVERGENCE PROBE (UTC vs America/Los_Angeles) ===
tz_utc_threshold: 2026-08-10 counted=0
tz_la_threshold: 2026-08-09 counted=0
tz_local_threshold: 2026-08-10
tz_divergence: OBSERVED — calendar find cut is timezone-dependent; publish TZ with the figure
tz_probe: PASS (informational; does not fail cold_verify)

=== DELETION TIMER PROBE ===
settings.json: missing
grep_cleanupPeriodDays_exit: 2  (watched RED / nonzero on missing file)
control_note: no settings file → default 30-day cleanup applies per Claude Code docs.
control_watched_red: PASS

=== ANTI-CONFLATION (wrong object must not look like retention) ===
wrote 2721 records into /tmp/transcripto-cold-tonight2/wrong-object-authorship-gate/retention-gate.jsonl
wrong_object_files: 1
wrong_object_records: 2721
wrong_object_old30_files: 0
anti_conflation: PASS — 2721 records in 1 file ≠ 2721 files (retention object)

=== PRODUCT BOUNDARY (transcripto has no file-age retention command) ===
product_boundary: PASS — CLI help has no file-age retention verb
help_exit: 0

=== STATS NEAR-MISS (message counts ≠ file-age) ===
stats_exit: 0
stats_home: /tmp/transcripto-cold-tonight2/fake-home-stats (isolated; does not touch ~/.trace)
stats_out:
2,721 of the 2,721 messages in your index are things you typed.  100.0%
the rest is the machine answering. `coach` counts raw transcript records instead
  of indexed messages, so its share is smaller; same numerator, wider population.

where you typed them

files your prompts moved most

stats_near_miss: DETECTED — stats output contains 2721 (retention denominator lookalike)
stats_near_miss_ruling: do NOT quote stats as retention evidence
stats_near_miss_probe: PASS (informational embarrassment hunt)

=== STEP 0 · small-n gate ===
STEP 0 — small-n gate (9 synthetic transcripts)

  ok    9 episodes extracted
  ok    rankable_corpus is false
  ok    honest refusal message printed
  ok    no SURVIVES MOST table
  ok    no SURVIVES LEAST table
  ok    no pattern denominator (x/y) below MIN_PATTERN_N
  ok    raw survival line still shown

7/7 green.
STEP 0: PASS

=== AUTHORSHIP GATE (fixtures-coach) — not the retention story ===
naive type:user count: 12
transcripto human_turns (gated): 8
total_records: 21 (naive line scan saw 21)
baseline: naive overcounts (gate is stricter) — expected

=== PRIVACY ===
privacy_mode: git-worktree
PRIVACY OK: 0 hits in 213 tracked files
privacy on real tree: PASS
PRIVACY FAIL: git ls-files returned 0 files (empty index is not a clean tree)
privacy_empty_index_exit: 1
privacy_empty_index_watched_red: PASS

=== SUITES ===
test_coach.sh → exit 0 · 15/15 green.
test_codex.sh → exit 0 · 14/14 green.
test_cost.sh → exit 0 · 12/12 green.
test_label_bands.sh → exit 0 · OK
test_small_n.sh → exit 0 · 7/7 green.
test_cursor_partial.sh → exit 0 · 7/7 green.
test_correction.sh → exit 0 · 32/32 green.
test_version.sh → exit 0 · green.

offline_core: PASS

=== NETWORK PROBES (optional; absence must not paint retention green) ===
docs_object: https://code.claude.com/docs/en/settings-reference.md
cleanupPeriodDays_default_line: * **Default**: `30`
desktopSessionCleanupPeriodDays_default_line: * **Default**: `0`, which sets no age limit
docs_cleanupPeriodDays_default_30: PASS (re-derived from settings-reference.md)
docs_desktop_default_0_no_age_limit: PASS
pypi_transcripto_version: 0.2.0 (re-derived)

cold_verify: PASS
```

## Archive stranger (tonight)

```sh
bash scripts/archive_stranger.sh
```

Re-derived snippet from tonight's archive run:

```text
=== ARCHIVE STRANGER · 2026-09-09T00:09:46Z ===
source_repo: /workspace
archive_has_git: no
ratio_30d: 504 of 2721
negative_planter: PASS — watched RED (wrong plant does not satisfy 504/2721)
independent_oracle: PASS
tz_divergence: OBSERVED — calendar find cut is timezone-dependent; publish TZ with the figure
stats_near_miss: DETECTED — stats output contains 2721 (retention denominator lookalike)
privacy_mode: archive-extract (no .git) — ephemeral git add -A for scan
offline_core: PASS
cold_verify: PASS
```

## Wheel stranger (tonight)

```sh
bash scripts/wheel_stranger.sh
```

```text
=== WHEEL STRANGER · 2026-09-09T00:11:45Z ===
source_repo: /workspace
work: /tmp/transcripto-wheel-stranger-1eIMZF

wheel: /tmp/transcripto-wheel-stranger-1eIMZF/wheels/transcripto-0.2.0-py3-none-any.whl

archive_has_git: no
wheel_install: transcripto 0.2.0

=== CWD SHADOW TRAP (source checkout on sys.path[0]) ===
import_from_repo_cwd: /workspace/transcripto.py
cwd_shadow_trap: DETECTED — import transcripto from repo cwd binds the TREE, not the wheel
cwd_shadow_trap_ruling: never verify a wheel install while cwd is the source checkout

=== WHEEL IMPORT FROM CLEAN CWD ===
transcripto.__file__: /tmp/transcripto-wheel-stranger-1eIMZF/venv/lib/python3.12/site-packages/transcripto.py
import_source: wheel site-packages OK

fixture_files_written: 2721 old_planted: 504
threshold_30d: 2026-08-10
ratio_30d: 504 of 2721
older_than_45d: 0
ASSERT fixture 504 of 2721 (old45=0): PASS
help_mentions_file_age_exit0: 1  (1 means no — expected)
transcripto_retention_exit: 2  (nonzero expected)
product_boundary_wheel: PASS
stats_exit: 0
stats_out_head:
2,721 of the 2,721 messages in your index are things you typed.  100.0%
the rest is the machine answering. `coach` counts raw transcript records instead
  of indexed messages, so its share is smaller; same numerator, wider population.
stats_near_miss: DETECTED on wheel arm — do not quote as retention
not_importing_archive_extract: PASS
wheel_stranger: PASS
```

## Pip-only baseline (tonight)

```sh
bash scripts/pip_only_baseline.sh
```

```text
=== PIP-ONLY BASELINE · 2026-09-09T00:09:46Z ===
repo: /workspace
work: /tmp/transcripto-pip-only-5hEKka
note: this arm installs from PyPI; it is NOT a measure of transcripto source in this arm

pip_only_version: transcripto 0.2.0
transcripto.__file__: /tmp/transcripto-pip-only-5hEKka/venv/lib/python3.12/site-packages/transcripto.py
import_source: site-packages OK

=== ARM A · retention (file ages) ===
fixture_files_written: 2721
naive_find_ratio: 504 of 2721 (threshold 2026-08-10)
help_mentions_file_age_exit0: 1  (1 means no — expected)
transcripto_retention_exit: 2  (nonzero expected — no such command)
transcripto_stats_exit: 0
stats_out_head:
2,721 of the 2,721 messages in your index are things you typed.  100.0%
the rest is the machine answering. `coach` counts raw transcript records instead
  of indexed messages, so its share is smaller; same numerator, wider population.

where you typed them
stats_near_miss: DETECTED on pip-only arm
arm_a_ruling: naive find WINS retention; pip-only transcripto cannot answer file-age

=== ARM B · authorship (pip-only coach vs naive) ===
naive_type_user: 12
pip_only_human_turns: 8
arm_b_ruling: naive wins simplicity; pip-only gate is stricter (8 < 12) — expected

pip_only_baseline: PASS
```

## Embarrassment hunt (retention claim)

0. **Main at start of tonight:** empty `git init` + `test_privacy.sh` exited **0**
   with `PRIVACY OK: 0 hits in 0 tracked files`. Fixed fail-closed; watched RED
   inside cold_verify (`privacy_empty_index_exit: 1`).
1. **CI docs probe pipefail.** `printf | awk` under `set -o pipefail` exited 1
   on GitHub Actions with `printf: write error: Broken pipe` when awk exited
   early on the settings-reference page. Locally the same pipe often exited 0
   (buffer timing). Fixed by writing the page to a file then awk-ing the file.
   This is the "control that looked green on my machine" failure mode.
2. **CWD shadows the wheel.** After `pip install` of a local wheel into a fresh
   venv, `import transcripto` from the source checkout cwd bound
   `/workspace/transcripto.py`, not site-packages. `cwd_shadow_trap: DETECTED`.
   Wheel proof requires a clean cwd (as `pip_only_baseline` already did).
3. **Archive stranger is the bigger object than clone.**
   `bash scripts/archive_stranger.sh` → PASS via ephemeral privacy index.
4. **Planter/assert is circular.** Independent oracle (180 blind ages,
   find == Python `st_mtime`) is the method control. Tonight:
   `independent_oracle: PASS` (python/find old30=88, old45=45).
5. **Negative planter watched RED.** Planted 503 of 2720; the 504/2721 assert
   would reject it (`negative_planter: PASS`).
6. **Anti-conflation:** 2721 records in 1 file ≠ 2721 files.
7. **`stats` near-miss DETECTED tonight:** on the retention fixture,
   `transcripto stats` printed `2,721 of the 2,721 messages… typed`. That
   number matches the retention denominator while measuring indexed messages.
   Do not quote it as retention evidence. Same DETECTED on pip-only and wheel.
8. **Exact Oscar counts are not cold-reproducible.** No `~/.claude/projects` on
   this VM (OQ-1).
9. **Two frozen stamps disagree** (504/2721 vs 579/2874). No death rate from delta.
10. **`older_than_45d == 0`** on the fixture (and was the sharper live fact).
11. **Naive `find` wins retention simplicity.** `product_boundary: PASS` on
    clone, pip-only, and wheel.
12. **Calendar midnight ≠ duration age.** `duration_vs_calendar=0` tonight.
13. **TZ divergence OBSERVED.** UTC threshold `2026-08-10` vs America/Los_Angeles
    `2026-08-09`. Publish timezone with any live figure.
14. **Docs object re-derived:** `cleanupPeriodDays` Default **30**; desktop
    `desktopSessionCleanupPeriodDays` Default **0** (no age limit). Do not
    collapse CLI and Desktop into one sentence.
15. **Green-on-outage traps watched RED:** missing settings → grep exit 2;
    empty git index → privacy exit 1.
16. **Prior night-wave branches never landed on main.** Main at start tonight
    still had no `docs/`, no `scripts/`, and the empty-index privacy green.
    Copying yesterday's PASS lines would have laundered a branch that was not
    the ship surface.

## Oscar morning re-derive (live corpus)

On a machine that has the corpus:

```sh
ROOT=~/.claude/projects
THIRTY=$(date -d '30 days ago' +%Y-%m-%d)
echo "$(find "$ROOT" -name '*.jsonl' ! -newermt "$THIRTY" | wc -l) of $(find "$ROOT" -name '*.jsonl' | wc -l)"
echo "TZ=$(date +%Z)"
```

Compare to the frozen quotes. Do not edit this doc's fixture PASS line to match
live counts — that would launder a different object into the cold artifact.
