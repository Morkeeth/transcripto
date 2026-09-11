# Cold verify artifact — 2026-09-11

Stranger one-command path for the **file-age retention method** behind
Oscar's frozen quote "504 of 2,721 files older than 30 days."

This VM has no `~/.claude/projects`. Tonight's PASS is **method + arithmetic
fixture + independent oracle + RED controls**, not a live re-derive of Oscar's
corpus. Live numbers remain machine-local (OQ-1).

## One command (cold stranger)

```sh
bash scripts/cold_verify.sh
```

Optional keep-work: `TRANSCRIPTO_COLD_DIR=/tmp/transcripto-cold-tonight bash scripts/cold_verify.sh`

Also exercised tonight:

```sh
bash scripts/archive_stranger.sh   # git-archive extract; no .git
bash scripts/wheel_stranger.sh     # local wheel, clean cwd
bash scripts/pip_only_baseline.sh  # naive find vs PyPI 0.2.0
```

## Command output (tonight, RUN)

Host `TZ=UTC`. Tip before docs commit: `3724c80` (scripts); this artifact
captures the re-run that includes the inverse TZ pair-trap detector.

```
=== COLD VERIFY · 2026-09-11T00:15:43Z ===
repo: /workspace
work: /tmp/transcripto-cold-tonight

transcripto: transcripto 0.2.0

=== OFFLINE CORE (proxies poisoned to 127.0.0.1:9) ===

generating fixture: 2721 jsonl files (504 aged 31–44d)…
fixture_files_written: 2721 old_planted: 504
retention source: FIXTURE /tmp/transcripto-cold-tonight/fixtures-retention-504-of-2721
  (no live ~/.claude/projects on this machine — method + arithmetic only)

=== RETENTION (find method, re-derived) ===
mode: fixture
as_of: 2026-09-11T00:15:49Z
threshold_30d: mtime <= 2026-08-12
threshold_45d: mtime <= 2026-07-28
total_jsonl: 2721
older_than_30d: 504
older_than_45d: 0
ratio_30d: 504 of 2721
oldest_mtime: 2026-07-29T00:15:46Z

frozen_quote (Oscar 2026-08-28, NOT re-derived on this VM unless mode=live): 504 of 2,721
frozen_rederive (Oscar 2026-08-29, NOT re-derived here): 579 of 2,874
NOTE: the two frozen stamps do not reconcile by arithmetic; no daily death rate is claimed.

ASSERT fixture 504 of 2721 (old45=0): PASS

=== NEGATIVE PLANTER (must go RED — control that can fail) ===
negative_plant: 503 of 2720 (deliberately not 504 of 2721)
negative_planter_assert_would_reject: YES (got 503 of 2720)
negative_planter: PASS — watched RED (wrong plant does not satisfy 504/2721)

=== INDEPENDENT ORACLE (find ↔ Python mtime, blind ages) ===
oracle_files: 180
oracle_age_days_min_max: 0 60
oracle_python_old30: 103
oracle_find_old30: 103
oracle_python_old45: 44
oracle_find_old45: 44
independent_oracle: PASS
(seed Random(20260911) — not the retention quote; collision guard active)

=== BOUNDARY PROBE (exactly at threshold) ===
boundary_probe: PASS — ! -newermt means mtime <= threshold midnight
duration_vs_calendar: file aged exactly 30*86400s counted_by_bang_newermt=0
  (calendar method is stricter than pure duration at this clock)

=== CALENDAR↔DURATION DELTA (full retention root) ===
calendar_old30: 504
duration_old30: 504
both_methods: 504
calendar_only: 0
duration_only: 0
method_skew_seconds: 950
calendar_duration_delta: none tonight — both methods agree on this root at this clock
calendar_duration_probe: PASS
(NOTE: planted ages are 31–44d, far from the 950s skew window. The single
 duration-aged boundary file above was NOT counted by calendar. Agreement on
 the fixture does not erase the boundary caveat.)

=== TOUCH↔UTIME PLANTER (shell touch -d vs os.utime) ===
touch_planter_old30: 7 of 10
utime_planter_old30: 7 of 10
ages_days: 28 29 30 31 32 33 40 44 45 50
touch_utime_planter: PASS — find counts agree (7)

=== TZ DIVERGENCE PROBE (multi-zone calendar cut) ===
tz_utc_threshold: 2026-08-12 counted=0
tz_la_threshold: 2026-08-11 counted=0
tz_tokyo_threshold: 2026-08-12 counted=0
tz_london_threshold: 2026-08-12 counted=0
tz_divergence: OBSERVED — 2 distinct calendar cuts tonight; publish TZ with the figure
tz_pair_trap: DETECTED — UTC↔Tokyo agree (2026-08-12) while LA differs (2026-08-11)
tz_pair_trap_ruling: which pair you pick decides whether divergence looks absent
(Beyond floor vs prior wave: prior trap was UTC↔LA agree / Tokyo differs.
 Tonight the inverse fired. A detector that only watches one pair would have
 missed this and printed no trap.)

=== FROZEN-QUOTE NON-RECONCILIATION (no unique death rate) ===
frozen_a_2026-08-28: 504 of 2721
frozen_b_2026-08-29: 579 of 2874
delta_old: +75
delta_total: +153
model_only_young_additions: REJECTED
model_only_aging_no_churn: REJECTED
model_unique_daily_death_rate: UNDERDETERMINED
frozen_quote_reconcile: FAIL-TO-RECONCILE
frozen_quote_ruling: do not print a daily deletion rate from 504/2721 → 579/2874

=== DELETION TIMER / ANTI-CONFLATION / PRODUCT BOUNDARY ===
control_watched_red: PASS (grep on missing settings → nonzero)
anti_conflation: PASS — 2721 records in 1 file ≠ 2721 files
product_boundary: PASS — CLI help has no file-age retention verb

=== STATS NEAR-MISS ===
stats_near_miss: DETECTED — stats output contains 2721 (retention denominator lookalike)
stats_near_miss_ruling: do NOT quote stats as retention evidence

=== STEP 0 / AUTHORSHIP (separate object) / PRIVACY ===
STEP 0: PASS (7/7 green)
naive type:user count: 12
transcripto human_turns (gated): 8
privacy on real tree: PASS
privacy_empty_index_exit: 1
privacy_empty_index_watched_red: PASS

=== SUITES ===
test_coach / codex / cost / label_bands / small_n / cursor_partial / correction / version → all green

offline_core: PASS

=== NETWORK PROBES ===
docs_object: https://code.claude.com/docs/en/settings-reference.md
cleanupPeriodDays_default_line: * **Default**: `30`
desktopSessionCleanupPeriodDays_default_line: * **Default**: `0`, which sets no age limit
docs_cleanupPeriodDays_default_30: PASS
docs_desktop_default_0_no_age_limit: PASS
pypi_transcripto_version: 0.2.0 (re-derived)

cold_verify: PASS
```

## Archive / wheel / pip-only (tonight)

```
$ bash scripts/archive_stranger.sh
archive_has_git: no
privacy_mode: archive-extract …
cold_verify: PASS

$ bash scripts/wheel_stranger.sh
cwd_shadow_trap: DETECTED — import from repo cwd binds the TREE
import_source: wheel site-packages OK (clean cwd)
ratio_30d: 504 of 2721
product_boundary_wheel: PASS
stats_near_miss: DETECTED on wheel arm
wheel_stranger: PASS

$ bash scripts/pip_only_baseline.sh
naive_find_ratio: 504 of 2721
transcripto_retention_exit: 2
stats_near_miss: DETECTED on pip-only arm
arm_a_ruling: naive find WINS retention
pip_only_human_turns: 8
pip_only_baseline: PASS
```

## What this does NOT prove

- Oscar's live 504/2721 on his machine (no corpus here).
- A unique daily deletion rate between the two frozen stamps.
- That calendar and duration methods always agree (boundary file disagreed;
  fixture ages sit outside the skew window).
- That transcripto answers file-age retention (it does not — naive `find` wins).
