# Cold verify — 2026-08-30 artifact (re-run 2026-09-06)

**One command (cold stranger, no key, no Oscar corpus):**

```sh
bash scripts/cold_verify.sh
```

**Prerequisite on Debian/Ubuntu cloud images:** `python3-venv`
(`sudo apt install python3.12-venv`). Without it, `python3 -m venv` fails.

## What this verifies

The **file-age method** behind the retention story:

```sh
ROOT=~/.claude/projects   # or the generated fixture on a cloud VM
THIRTY=$(date -d '30 days ago' +%Y-%m-%d)
TOTAL=$(find "$ROOT" -name '*.jsonl' | wc -l)
OLD30=$(find "$ROOT" -name '*.jsonl' ! -newermt "$THIRTY" | wc -l)
echo "$OLD30 of $TOTAL older than 30d (as of $THIRTY)"
```

**Object:** jsonl **files** under a projects root, aged by mtime.
**Not** an authorship-gate count of human turns. Prior night waves that
treated 504/2721 as `coach` kept-turns were measuring the wrong object.

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
(so the 45-day count stays 0), and asserts exact equality.

That planter/assert alone is circular. Tonight's script also runs an
**independent oracle**: 180 files with blind ages 0–60 days, expected counts
from Python `st_mtime` vs `find ! -newermt`, plus a midnight boundary probe.

## Captured output

Command run tonight: `bash scripts/cold_verify.sh` (exit 0).

```text
=== COLD VERIFY · 2026-09-06T00:14:01Z ===
repo: /workspace
work: /tmp/transcripto-cold-verify-lok3wL

transcripto: transcripto 0.2.0

generating fixture: 2721 jsonl files (504 aged 31–44d)…
retention source: FIXTURE /tmp/transcripto-cold-verify-lok3wL/fixtures-retention-504-of-2721
  (no live ~/.claude/projects on this machine — method + arithmetic only)

=== RETENTION (find method, re-derived) ===
mode: fixture
as_of: 2026-09-06T00:14:10Z
threshold_30d: mtime <= 2026-08-07
threshold_45d: mtime <= 2026-07-23
total_jsonl: 2721
older_than_30d: 504
older_than_45d: 0
ratio_30d: 504 of 2721
oldest_file: /tmp/transcripto-cold-verify-lok3wL/fixtures-retention-504-of-2721/demo-project/sessions/session-0055.jsonl
oldest_mtime: 2026-07-24T00:14:06Z

frozen_quote (Oscar 2026-08-28, NOT re-derived on this VM unless mode=live): 504 of 2,721
frozen_rederive (Oscar 2026-08-29, NOT re-derived here): 579 of 2,874
NOTE: the two frozen stamps do not reconcile by arithmetic; no daily death rate is claimed.

ASSERT fixture 504 of 2721 (old45=0): PASS

=== INDEPENDENT ORACLE (find ↔ Python mtime, blind ages) ===
oracle_files: 180
oracle_age_days_min_max: 0 60
oracle_python_old30: 90
oracle_find_old30: 90
oracle_python_old45: 47
oracle_find_old45: 47
threshold_30d_epoch: 1786060800.0
threshold_45d_epoch: 1784764800.0
independent_oracle: PASS

=== BOUNDARY PROBE (exactly at threshold) ===
threshold_midnight_epoch: 1786060800 (2026-08-07 00:00:00 local)
counted_by_bang_newermt at_midnight: 1   (expect 1 — mtime == ref is NOT newer)
counted_by_bang_newermt one_sec_after: 0   (expect 0 — strictly newer)
counted_by_bang_newermt one_sec_before: 1   (expect 1)
boundary_probe: PASS — ! -newermt means mtime <= threshold midnight
duration_vs_calendar: file aged exactly 30*86400s counted_by_bang_newermt=0
  (0 means calendar method is stricter than pure duration at this clock time;
   1 means the duration-aged file already sits on/before threshold midnight)
caveat: article find method uses calendar midnight, not age_seconds > 30*86400

=== DELETION TIMER PROBE ===
settings.json: missing
grep_cleanupPeriodDays_exit: 2  (watched RED / nonzero on missing file)
control_note: no settings file → default 30-day cleanup applies per Claude Code docs.
control_watched_red: PASS
docs_object: https://code.claude.com/docs/en/settings-reference.md
cleanupPeriodDays_default_line: * **Default**: `30`
desktopSessionCleanupPeriodDays_default_line: * **Default**: `0`, which sets no age limit
docs_cleanupPeriodDays_default_30: PASS (re-derived from settings-reference.md)
docs_desktop_default_0_no_age_limit: PASS

=== ANTI-CONFLATION (wrong object must not look like retention) ===
wrote 2721 records into /tmp/transcripto-cold-verify-lok3wL/wrong-object-authorship-gate/retention-gate.jsonl
wrong_object_files: 1
wrong_object_records: 2721
wrong_object_old30_files: 0
anti_conflation: PASS — 2721 records in 1 file ≠ 2721 files (retention object)

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
PRIVACY OK: 0 hits in 214 tracked files
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

cold_verify: PASS
```

## Embarrassment hunt (retention claim)

0. **Circular planter (caught and fixed tonight):** asserting 504/2721 after
   planting 504/2721 only proves the planter. The **independent oracle**
   (180 blind ages, find ↔ Python `st_mtime`) is the method control. Script
   prints `independent_oracle: PASS` and `boundary_probe: PASS`.
1. **Anti-conflation control:** a single jsonl with 2721 records yields
   `find` file count **1**, not 2721. Record-count gates are not the retention
   object. Script prints `anti_conflation: PASS`.
2. **Wrong object (prior waves):** some branches treated 504/2721 as
   authorship-gate kept-turns via `coach`. The article claim is **file ages**.
3. **Exact Oscar counts are not cold-reproducible.** This VM has no
   `~/.claude/projects`. Shipping method + arithmetic fixture + oracle is
   honest; claiming live 504/2721 from a stranger clone would be false.
4. **Two frozen stamps disagree** (504/2721 vs 579/2874). Do not invent a
   death rate from the delta.
5. **`older_than_45d == 0`** is the sharper fact — the window already cut.
6. **Naive `find` wins the retention story on simplicity.** Transcripto does
   not compute file-age retention; see `docs/BASELINE-ARM.md`.
7. **Green-on-outage traps watched RED tonight:**
   - missing `settings.json` → `grep cleanupPeriodDays` exit 2
   - empty `git init` → `test_privacy.sh` exit 1
8. **Calendar midnight ≠ duration age.** Tonight a file aged exactly
   `30*86400` seconds was **not** counted by `! -newermt` (counted=0) because
   its clock time still sat after threshold midnight on the same calendar day.
   The article `find` method is a calendar-day cut, not a pure duration cut.
   Script prints `duration_vs_calendar` and the caveat line.
9. **Docs object opened tonight**
   (`https://code.claude.com/docs/en/settings-reference.md`):
   - `cleanupPeriodDays` **Default: 30**
   - `desktopSessionCleanupPeriodDays` **Default: 0** (no age limit for
     Desktop/Cowork until that key is set; deletion then requires exceeding
     *both* limits). Do not collapse CLI and Desktop retention into one
     sentence.

## Oscar morning re-derive (live corpus)

On a machine that has the corpus:

```sh
ROOT=~/.claude/projects
THIRTY=$(date -d '30 days ago' +%Y-%m-%d)
echo "$(find "$ROOT" -name '*.jsonl' ! -newermt "$THIRTY" | wc -l) of $(find "$ROOT" -name '*.jsonl' | wc -l)"
```

Compare to the frozen quotes. Do not edit this doc's fixture PASS line to match
live counts — that would launder a different object into the cold artifact.
