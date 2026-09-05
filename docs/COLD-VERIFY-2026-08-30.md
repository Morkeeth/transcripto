# Cold verify — 2026-08-30 artifact (re-run 2026-09-05)

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

## Captured output

Command run tonight: `bash scripts/cold_verify.sh` (exit 0).

```text
=== COLD VERIFY · 2026-09-05T00:15:57Z ===
repo: /workspace
work: /tmp/transcripto-cold-verify-gTIYXg

transcripto: transcripto 0.2.0

generating fixture: 2721 jsonl files (504 aged 31–44d)…
retention source: FIXTURE /tmp/transcripto-cold-verify-gTIYXg/fixtures-retention-504-of-2721
  (no live ~/.claude/projects on this machine — method + arithmetic only)

=== RETENTION (find method, re-derived) ===
mode: fixture
as_of: 2026-09-05T00:16:06Z
threshold_30d: mtime <= 2026-08-06
threshold_45d: mtime <= 2026-07-22
total_jsonl: 2721
older_than_30d: 504
older_than_45d: 0
ratio_30d: 504 of 2721
oldest_file: /tmp/transcripto-cold-verify-gTIYXg/fixtures-retention-504-of-2721/demo-project/sessions/session-0055.jsonl
oldest_mtime: 2026-07-23T00:16:02Z

frozen_quote (Oscar 2026-08-28, NOT re-derived on this VM unless mode=live): 504 of 2,721
frozen_rederive (Oscar 2026-08-29, NOT re-derived here): 579 of 2,874
NOTE: the two frozen stamps do not reconcile by arithmetic; no daily death rate is claimed.

ASSERT fixture 504 of 2721 (old45=0): PASS

=== DELETION TIMER PROBE ===
settings.json: missing
grep_cleanupPeriodDays_exit: 2  (watched RED / nonzero on missing file)
control_note: no settings file → default 30-day cleanup applies per Claude Code docs.
control_watched_red: PASS

=== ANTI-CONFLATION (wrong object must not look like retention) ===
wrote 2721 records into /tmp/transcripto-cold-verify-gTIYXg/wrong-object-authorship-gate/retention-gate.jsonl
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
PRIVACY OK: 0 hits in 208 tracked files
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

0. **Anti-conflation control (ran tonight):** a single jsonl with 2721 records
   (504 typed + disguised `type:user` rows) yields `find` file count **1**, not
   2721. Record-count gates are not the retention object. Script prints
   `anti_conflation: PASS`.
 (retention claim)

1. **Wrong object (prior waves):** some branches treated 504/2721 as authorship-gate
   kept-turns via `coach`. The article claim is **file ages**. Measuring the proxy
   produces a confident false verification.
2. **Exact Oscar counts are not cold-reproducible.** This VM has no
   `~/.claude/projects`. Shipping method + arithmetic fixture is honest;
   claiming live 504/2721 from a stranger clone would be false.
3. **Two frozen stamps disagree** (504/2721 vs 579/2874). Do not invent a death
   rate from the delta.
4. **`older_than_45d == 0`** is the sharper fact — the window already cut.
5. **Naive `find` wins the retention story on simplicity.** Transcripto does not
   compute file-age retention; see `docs/BASELINE-ARM.md`.
6. **Green-on-outage traps watched RED tonight:**
   - missing `settings.json` → `grep cleanupPeriodDays` exit 2
   - empty `git init` → `test_privacy.sh` exit 1 (was exit 0 before tonight's fix)
7. **Desktop/Cowork** has a *separate* setting key
   (`desktopSessionCleanupPeriodDays` per Claude Code sessions docs). Do not
   collapse CLI and Desktop retention into one sentence without opening that
   object. Default for the Desktop key was not re-derived as a number tonight
   (pages fetched list the key; CLI `cleanupPeriodDays` default **30** is
   documented at https://code.claude.com/docs/en/sessions.md).

## Oscar morning re-derive (live corpus)

On a machine that has the corpus:

```sh
ROOT=~/.claude/projects
THIRTY=$(date -d '30 days ago' +%Y-%m-%d)
echo "$(find "$ROOT" -name '*.jsonl' ! -newermt "$THIRTY" | wc -l) of $(find "$ROOT" -name '*.jsonl' | wc -l)"
```

Compare to the frozen quotes. Do not edit this doc's fixture PASS line to match
live counts — that would launder a different object into the cold artifact.
