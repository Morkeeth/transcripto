# Cold verify — 2026-08-30 artifact (re-run 2026-09-10)

**One command (cold stranger, no key, no Oscar corpus):**

```sh
bash scripts/cold_verify.sh
```

**Prerequisite on Debian/Ubuntu cloud images:** `python3-venv`
(`sudo apt install python3.12-venv`). Without it, `python3 -m venv` fails.
System `pip install -e .` may also fail under PEP 668; the script uses its own venv.

**Archive stranger (no `.git`):**

```sh
bash scripts/archive_stranger.sh
```

**Wheel stranger (local wheel, offline install, clean cwd):**

```sh
bash scripts/wheel_stranger.sh
```

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
**Not** an authorship-gate count of human turns. **Not** `transcripto stats`
message counts (tonight those printed `2,721 of the 2,721 messages … 100.0%`
on the retention fixture — a near-miss that must not be quoted as retention).

Frozen Oscar quotes (machine-local; **not** re-derived on this VM):

| stamp | figure | note |
|-------|--------|------|
| 2026-08-28 | 504 of 2,721 | weekly review freeze |
| 2026-08-29 | 579 of 2,874 | same `find` method next day |

The two stamps do not reconcile by arithmetic. Delta old30 = **+75**, delta
total = **+153**. Total rose, so this is not a deletion day. No daily death
rate is claimed; tonight's `death_rate_impossible` control refuses the
laundered figure **75**.

The sharper companion fact on Oscar's machine was `older_than_45d == 0` —
deletion already happened; it is not a future risk only.

When `~/.claude/projects` is absent, the script generates an
**arithmetic-faithful fixture**: 2721 files, 504 touched to ages 31–44 days
(so the 45-day count stays 0), and asserts exact equality. A **negative
planter** (503 of 2720) must fail that assert. An **independent oracle**
(180 blind ages, seed `20260910`) compares find ↔ Python mtime without sharing
the 504/2721 target.

## Docs object (re-derived tonight)

`curl` → `https://code.claude.com/docs/en/settings-reference.md`:

- `cleanupPeriodDays` **Default: `30`**
- `desktopSessionCleanupPeriodDays` **Default: `0`**, which sets **no age limit**
- Deletion runs as a **background sweep after a session starts** (not continuous)
- Desktop/Cowork transcripts are kept at any age by default — do not flatten
  "30-day deletion" onto Desktop sessions without checking the live mix (OQ-4)

## Captured output

Command run tonight: `bash scripts/cold_verify.sh` (exit 0).

```text
=== COLD VERIFY · 2026-09-10T12:17:48Z ===
repo: /workspace
work: /tmp/transcripto-cold-verify-tonight

transcripto: transcripto 0.2.0

=== OFFLINE CORE (proxies poisoned to 127.0.0.1:9) ===

generating fixture: 2721 jsonl files (504 aged 31–44d)…
fixture_files_written: 2721 old_planted: 504
retention source: FIXTURE /tmp/transcripto-cold-verify-tonight/fixtures-retention-504-of-2721
  (no live ~/.claude/projects on this machine — method + arithmetic only)

=== RETENTION (find method, re-derived) ===
mode: fixture
as_of: 2026-09-10T12:17:55Z
threshold_30d: mtime <= 2026-08-11
threshold_45d: mtime <= 2026-07-27
total_jsonl: 2721
older_than_30d: 504
older_than_45d: 0
ratio_30d: 504 of 2721
oldest_file: /tmp/transcripto-cold-verify-tonight/fixtures-retention-504-of-2721/demo-project/sessions/session-0055.jsonl
oldest_mtime: 2026-07-28T12:17:52Z

frozen_quote (Oscar 2026-08-28, NOT re-derived on this VM unless mode=live): 504 of 2,721
frozen_rederive (Oscar 2026-08-29, NOT re-derived here): 579 of 2,874
NOTE: the two frozen stamps do not reconcile by arithmetic; no daily death rate is claimed.

ASSERT fixture 504 of 2721 (old45=0): PASS

=== DEATH-RATE IMPOSSIBILITY (frozen stamps are quotes, not live) ===
frozen_delta_old30: +75
frozen_delta_total: +153
laundered_death_claim_if_printed: 75 (FORBIDDEN)
death_rate_impossible: PASS — total rose and old30 rose; refuse daily death rate

=== EMPTY-GREP CONTROL (outage must not read clean) ===
empty_input_grep_q_dot_exit: 1  (expect 1)
empty_grep_control: PASS — exit 1 on empty; callers must not treat that as CLEAN without a non-empty guard

=== NEGATIVE PLANTER (must go RED — control that can fail) ===
fixture_files_written: 2720 old_planted: 503
negative_plant: 503 of 2720 (deliberately not 504 of 2721)
negative_planter_assert_would_reject: YES (got 503 of 2720)
negative_planter: PASS — watched RED (wrong plant does not satisfy 504/2721)

=== INDEPENDENT ORACLE (find ↔ Python mtime, blind ages) ===
oracle_files: 180
oracle_age_days_min_max: 0 60
oracle_python_old30: 96
oracle_find_old30: 96
oracle_python_old45: 45
oracle_find_old45: 45
threshold_30d_epoch: 1786406400.0
threshold_45d_epoch: 1785110400.0
independent_oracle: PASS

=== BOUNDARY PROBE (exactly at threshold) ===
threshold_midnight_epoch: 1786406400 (2026-08-11 00:00:00 local)
counted_by_bang_newermt at_midnight: 1   (expect 1 — mtime == ref is NOT newer)
counted_by_bang_newermt one_sec_after: 0   (expect 0 — strictly newer)
counted_by_bang_newermt one_sec_before: 1   (expect 1)
boundary_probe: PASS — ! -newermt means mtime <= threshold midnight
duration_vs_calendar: file aged exactly 30*86400s counted_by_bang_newermt=0
  (0 means calendar method is stricter than pure duration at this clock time;
   1 means the duration-aged file already sits on/before threshold midnight)
caveat: article find method uses calendar midnight, not age_seconds > 30*86400

=== TZ DIVERGENCE PROBE (UTC vs America/Los_Angeles) ===
tz_utc_threshold: 2026-08-11 counted=0
tz_la_threshold: 2026-08-11 counted=0
tz_local_threshold: 2026-08-11
tz_divergence: none at this clock (thresholds equal: 2026-08-11); still document TZ with live figures
tz_probe: PASS (informational; does not fail cold_verify)

=== DELETION TIMER PROBE ===
settings.json: missing
grep_cleanupPeriodDays_exit: 2  (watched RED / nonzero on missing file)
control_note: no settings file → default 30-day cleanup applies per Claude Code docs.
control_watched_red: PASS

=== ANTI-CONFLATION (wrong object must not look like retention) ===
wrote 2721 records into /tmp/transcripto-cold-verify-tonight/wrong-object-authorship-gate/retention-gate.jsonl
wrong_object_files: 1
wrong_object_records: 2721
wrong_object_old30_files: 0
anti_conflation: PASS — 2721 records in 1 file ≠ 2721 files (retention object)

=== PRODUCT BOUNDARY (transcripto has no file-age retention command) ===
product_boundary: PASS — CLI help has no file-age retention verb
help_exit: 0

=== STATS NEAR-MISS (message counts ≠ file-age) ===
stats_exit: 0
stats_home: /tmp/transcripto-cold-verify-tonight/fake-home-stats (isolated; does not touch ~/.trace)
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

offline_core: PASS

=== NETWORK PROBES (optional; absence must not paint retention green) ===
docs_object: https://code.claude.com/docs/en/settings-reference.md
cleanupPeriodDays_default_line: * **Default**: `30`
desktopSessionCleanupPeriodDays_default_line: * **Default**: `0`, which sets no age limit
docs_cleanupPeriodDays_default_30: PASS (re-derived from settings-reference.md)
docs_desktop_default_0_no_age_limit: PASS
docs_sweep_lag: PASS — deletion is a background sweep after session start, not continuous
docs_sweep_lag_ruling: files can sit past cleanupPeriodDays until the next session starts
docs_desktop_immortal_default: PASS — Desktop/Cowork default keeps transcripts at any age
docs_desktop_immortal_ruling: do not flatten '30-day deletion' onto Desktop sessions without checking the mix
pypi_transcripto_version: 0.2.0 (re-derived)

=== PYPI PACKAGE AUDIT (published wheel vs repo stranger path) ===
pypi_wheel: /tmp/transcripto-cold-verify-tonight/pypi-audit/transcripto-0.2.0-py3-none-any.whl
pypi_wheel_entries: 9
pypi_wheel_cold_verify_hits: 0
pypi_package_audit: PASS — published wheel has no cold_verify script
pypi_package_audit_ruling: stranger retention method requires the repo (clone/archive), not pip-only

cold_verify: PASS
work dir kept: /tmp/transcripto-cold-verify-tonight
```

## Archive stranger

```sh
bash scripts/archive_stranger.sh
```

Re-derived tonight: `archive_has_git: no` → nested `cold_verify: PASS`
(including `death_rate_impossible`, `independent_oracle`, `negative_planter`,
`empty_grep_control`, `offline_core`, docs sweep-lag, PyPI package audit).

## Wheel stranger

```sh
bash scripts/wheel_stranger.sh
```

Tonight: `cwd_shadow_trap: DETECTED` from repo cwd; clean-cwd wheel import OK;
`ratio_30d: 504 of 2721`; `stats_near_miss: DETECTED`; `wheel_stranger: PASS`.

## Remote stranger clone

```sh
git clone --depth 1 --branch cursor/night-wave-p1-launch-fcb9 \
  https://github.com/Morkeeth/transcripto.git /tmp/transcripto-stranger-clone
cd /tmp/transcripto-stranger-clone && bash scripts/cold_verify.sh
```

Tonight: **`cold_verify: PASS`** on a fresh remote clone (scripts-only tip;
docs landed in the same push as this artifact).

## Embarrassment hunt (tonight)

1. **Planter/assert is circular.** Independent oracle (seed 20260910) →
   python/find old30=**96**, old45=**45**. Negative planter 503/2720 watched RED.
2. **`stats` near-miss DETECTED:** on the retention fixture, stats prints
   `2,721 of the 2,721 messages … 100.0% typed` — same digits as the retention
   denominator. Do not quote as retention.
3. **Death-rate laundering refused:** +75 old / +153 total → printing "75 deaths"
   is forbidden (`death_rate_impossible: PASS`).
4. **Empty-grep outage class:** `printf '' | grep -q .` exits 1; callers must
   not treat that as CLEAN without a non-empty guard (`empty_grep_control: PASS`).
   Main's former privacy guard exited 0 on empty index — fixed tonight.
5. **Calendar ≠ duration:** file aged exactly `30*86400`s counted_by_bang_newermt=**0**
   tonight. Article method uses calendar midnight.
6. **TZ:** UTC and America/Los_Angeles agreed on `2026-08-11` at this clock;
   divergence is clock-dependent — still publish TZ with live figures.
7. **Desktop immortal default:** docs Default `0` / no age limit — article must
   not claim universal 30-day death without the CLI vs Desktop split.
8. **Sweep lag:** deletion is a background sweep after session start — files can
   sit past 30d until the next session.
9. **PyPI wheel has no `cold_verify`:** 0 hits in 9 entries. `pip install
   transcripto` alone cannot reproduce the stranger retention method; clone or
   archive the repo.
10. **CWD shadows the wheel.** Verifying a wheel install from the source
    checkout binds the TREE (`cwd_shadow_trap: DETECTED`).
11. **Naive `find` wins retention.** Transcripto has no file-age retention verb
    (`product_boundary: PASS`; pip-only `retention` exit 2).

## What this does not prove

- Oscar's live 504/2721 on his machine (OQ-1). Method + arithmetic only here.
- That Desktop sessions are or are not inside his `~/.claude/projects` mix (OQ-4).
- Anything about article/X/PyPI publish (OQ-3 — Oscar only).
