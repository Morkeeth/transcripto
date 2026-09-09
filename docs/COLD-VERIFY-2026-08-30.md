# Cold verify — file-age retention method

**Ran:** 2026-09-09T22:18:42Z · host TZ=`UTC` · branch tip at run time
**Command:** `TRANSCRIPTO_COLD_DIR=/tmp/transcripto-cold-tonight bash scripts/cold_verify.sh`
**Result:** `cold_verify: PASS` · `offline_core: PASS`

This document captures **tonight's command output**. It is not a copy of an
older PASS line. Oscar's live `~/.claude/projects` counts are **not** re-derived
on this VM (no corpus). The fixture proves the method + arithmetic; Oscar
re-runs `find` on his machine for the live quote.

## What the claim is (and is not)

| is | is not |
|----|--------|
| `find ROOT -name '*.jsonl' ! -newermt <30d-calendar>` file count | authorship / `human_turns` |
| mtime retention under a projects root | `transcripto stats` message counts |
| calendar midnight cut (`date -d '30 days ago'`) | pure `age_seconds > 30*86400` |

Frozen quotes (machine-local; **not** re-derived here unless `mode=live`):

- 2026-08-28: **504 of 2,721**
- 2026-08-29: **579 of 2,874**

Those two stamps **fail to reconcile** into a unique daily death rate (see
probe below). Do not print one.

## Stranger one-liner

```sh
bash scripts/cold_verify.sh
```

No key. No network after the one-time venv/pip bootstrap (offline core poisons
proxies). No Oscar corpus required.

## Tonight's output (abridged; full log 165 lines)

```
=== COLD VERIFY · 2026-09-09T22:18:42Z ===
repo: /workspace
work: /tmp/transcripto-cold-tonight

transcripto: transcripto 0.2.0

=== OFFLINE CORE (proxies poisoned to 127.0.0.1:9) ===

generating fixture: 2721 jsonl files (504 aged 31–44d)…
fixture_files_written: 2721 old_planted: 504
retention source: FIXTURE …/fixtures-retention-504-of-2721
  (no live ~/.claude/projects on this machine — method + arithmetic only)

=== RETENTION (find method, re-derived) ===
mode: fixture
as_of: 2026-09-09T22:18:49Z
threshold_30d: mtime <= 2026-08-10
threshold_45d: mtime <= 2026-07-26
total_jsonl: 2721
older_than_30d: 504
older_than_45d: 0
ratio_30d: 504 of 2721
oldest_mtime: 2026-07-27T22:18:46Z

ASSERT fixture 504 of 2721 (old45=0): PASS

=== NEGATIVE PLANTER (must go RED — control that can fail) ===
negative_plant: 503 of 2720 (deliberately not 504 of 2721)
negative_planter: PASS — watched RED (wrong plant does not satisfy 504/2721)

=== INDEPENDENT ORACLE (find ↔ Python mtime, blind ages) ===
oracle_files: 180
oracle_python_old30: 88
oracle_find_old30: 88
oracle_python_old45: 45
oracle_find_old45: 45
independent_oracle: PASS

=== BOUNDARY PROBE (exactly at threshold) ===
boundary_probe: PASS — ! -newermt means mtime <= threshold midnight
duration_vs_calendar: file aged exactly 30*86400s counted_by_bang_newermt=0
caveat: article find method uses calendar midnight, not age_seconds > 30*86400

=== TZ DIVERGENCE PROBE (multi-zone calendar cut) ===
tz_utc_threshold: 2026-08-10 counted=0
tz_la_threshold: 2026-08-10 counted=0
tz_tokyo_threshold: 2026-08-11 counted=0
tz_london_threshold: 2026-08-10 counted=0
tz_divergence: OBSERVED — 2 distinct calendar cuts tonight; publish TZ with the figure
tz_pair_trap: DETECTED — UTC↔LA agree (2026-08-10) while Tokyo differs (2026-08-11)
tz_pair_trap_ruling: a two-zone probe can miss divergence that a third zone catches

=== FROZEN-QUOTE NON-RECONCILIATION (no unique death rate) ===
frozen_a_2026-08-28: 504 of 2721
frozen_b_2026-08-29: 579 of 2874
delta_old: +75
delta_total: +153
model_only_young_additions: REJECTED (predicts delta_old=0; got +75)
model_only_aging_no_churn: REJECTED (predicts delta_total=0; got +153)
model_unique_daily_death_rate: UNDERDETERMINED (aged_in, creates, deletes free)
frozen_quote_reconcile: FAIL-TO-RECONCILE — no unique death rate from two stamps alone
frozen_quote_ruling: do not print a daily deletion rate from 504/2721 → 579/2874
frozen_quote_probe: PASS (embarrassment watched: non-reconciliation is the finding)

=== DELETION TIMER PROBE ===
settings.json: missing
grep_cleanupPeriodDays_exit: 2  (watched RED / nonzero on missing file)
control_watched_red: PASS

=== ANTI-CONFLATION ===
anti_conflation: PASS — 2721 records in 1 file ≠ 2721 files (retention object)

=== PRODUCT BOUNDARY ===
product_boundary: PASS — CLI help has no file-age retention verb

=== STATS NEAR-MISS ===
stats_out:
2,721 of the 2,721 messages in your index are things you typed.  100.0%
stats_near_miss: DETECTED — stats output contains 2721 (retention denominator lookalike)
stats_near_miss_ruling: do NOT quote stats as retention evidence

=== STEP 0 · small-n gate ===
7/7 green.
STEP 0: PASS

=== AUTHORSHIP GATE (fixtures-coach) — not the retention story ===
naive type:user count: 12
transcripto human_turns (gated): 8

=== PRIVACY ===
PRIVACY OK: 0 hits in 214 tracked files
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

=== NETWORK PROBES ===
docs_object: https://code.claude.com/docs/en/settings-reference.md
cleanupPeriodDays_default_line: * **Default**: `30`
desktopSessionCleanupPeriodDays_default_line: * **Default**: `0`, which sets no age limit
docs_cleanupPeriodDays_default_30: PASS (re-derived from settings-reference.md)
docs_desktop_default_0_no_age_limit: PASS
pypi_transcripto_version: 0.2.0 (re-derived)

cold_verify: PASS
```

## Sister arms (also ran tonight)

| arm | command | result |
|-----|---------|--------|
| Archive stranger | `bash scripts/archive_stranger.sh` | **PASS** (`archive_has_git: no`; ephemeral privacy index) |
| Wheel stranger | `bash scripts/wheel_stranger.sh` | **PASS** — `cwd_shadow_trap: DETECTED`; clean-cwd site-packages OK; fixture 504/2721 |
| Pip-only baseline | `bash scripts/pip_only_baseline.sh` | **PASS** — naive find wins retention; `retention` exit 2; stats near-miss DETECTED |
| Empty-index privacy | `./test_privacy_empty_index.sh` | **PASS** (exit 1 watched RED) |
| Unit tests | `python3 -m unittest discover -s tests -v` | **73 OK** |

## Embarrassment hunt (retention claim)

Findings that make us look worse, and are therefore the point:

1. **Naive `find` wins** the retention question. Transcripto has no file-age verb.
2. **`stats` near-miss:** on the retention fixture, `stats` prints `2,721 of the 2,721 messages…` — same denominator, wrong object.
3. **Main's privacy green-on-outage:** `git show origin/main:test_privacy.sh` in a fresh `git init` printed `PRIVACY OK: 0 hits in 0 tracked files` and exited **0**. Fixed tonight (fail-closed).
4. **TZ pair trap:** UTC↔LA agreed tonight (`2026-08-10`) while Tokyo differed (`2026-08-11`). A two-zone probe can miss divergence.
5. **Frozen quotes do not reconcile** into a unique daily death rate (`FAIL-TO-RECONCILE`).
6. **Wheel cwd-shadow:** verifying a wheel while cwd is the source tree binds `transcripto.py` from the tree, not site-packages.
7. **Calendar ≠ duration:** a file aged exactly `30*86400` seconds was **not** counted by `! -newermt` at this clock (`counted=0`).

## Oscar live re-derive (tomorrow)

```sh
echo "TZ=$(date +%Z) $(date -u +%Y-%m-%dT%H:%M:%SZ)"
THIRTY=$(date -d '30 days ago' +%Y-%m-%d)
echo "threshold=$THIRTY"
find ~/.claude/projects -name '*.jsonl' | wc -l
find ~/.claude/projects -name '*.jsonl' ! -newermt "$THIRTY" | wc -l
```

Compare to frozen 504/2721 and 579/2874. Print TZ. Do not invent a death rate.
