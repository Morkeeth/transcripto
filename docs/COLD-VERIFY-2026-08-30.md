# Cold verify artifact — 2026-09-12

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

## What "504 of 2721" means (object)

```sh
find "$ROOT" -type f -name '*.jsonl' | wc -l
find "$ROOT" -type f -name '*.jsonl' ! -newermt "$(date -d '30 days ago' +%Y-%m-%d)" | wc -l
```

Not authorship. Not `stats` message counts. Not human turns. Symlink-aware:
omit `-type f` and a single symlink inflates the total (watched tonight:
name-only=2, `-type f`=1).

## Command output (tonight, RUN)

Host `TZ=UTC`. Re-derived figures below — do not carry prior-wave oracle
counts (83/39 tonight ≠ prior-wave 103/44). Tip after this commit includes
the HEAD-archive privacy control.

```
=== COLD VERIFY · 2026-09-12T13:15:55Z ===
repo: /workspace
work: /tmp/transcripto-cold-final3

transcripto: transcripto 0.2.0

=== OFFLINE CORE (proxies poisoned to 127.0.0.1:9) ===

generating fixture: 2721 jsonl files (504 aged 31–44d)…
fixture_files_written: 2721 old_planted: 504
retention source: FIXTURE /tmp/transcripto-cold-final3/fixtures-retention-504-of-2721
  (no live ~/.claude/projects on this machine — method + arithmetic only)

=== RETENTION (find method, re-derived) ===
mode: fixture
as_of: 2026-09-12T13:16:02Z
threshold_30d: mtime <= 2026-08-13
threshold_45d: mtime <= 2026-07-29
total_jsonl: 2721
older_than_30d: 504
older_than_45d: 0
ratio_30d: 504 of 2721
oldest_file: /tmp/transcripto-cold-final3/fixtures-retention-504-of-2721/demo-project/sessions/session-0055.jsonl
oldest_mtime: 2026-07-30T13:15:59Z

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
empty_input_grep_qv_x_exit: 1  (expect 1 — prompt trap)
empty_grep_control: PASS — both -q and -qv exit 1 on empty; not CLEAN without a non-empty guard

=== SYMLINK INFLATION TRAP (omit -type f → inflated totals) ===
symlink_find_name_only: 2
symlink_find_type_f: 1
symlink_inflation: DETECTED — name-only find counted 2; -type f counted 1
symlink_inflation_ruling: retention method MUST use find -type f -name '*.jsonl'
symlink_inflation_probe: PASS

=== NEGATIVE PLANTER (must go RED — control that can fail) ===
fixture_files_written: 2720 old_planted: 503
negative_plant: 503 of 2720 (deliberately not 504 of 2721)
negative_planter_assert_would_reject: YES (got 503 of 2720)
negative_planter: PASS — watched RED (wrong plant does not satisfy 504/2721)

=== INDEPENDENT ORACLE (find ↔ Python mtime, blind ages) ===
oracle_files: 180
oracle_age_days_min_max: 1 60
oracle_python_old30: 83
oracle_find_old30: 83
oracle_python_old45: 39
oracle_find_old45: 39
threshold_30d_epoch: 1786579200.0
threshold_45d_epoch: 1785283200.0
independent_oracle: PASS
(seed Random(20260912) — not the retention quote; collision guard active)

=== BOUNDARY PROBE (exactly at threshold) ===
threshold_midnight_epoch: 1786579200 (2026-08-13 00:00:00 local)
counted_by_bang_newermt at_midnight: 1   (expect 1 — mtime == ref is NOT newer)
counted_by_bang_newermt one_sec_after: 0   (expect 0 — strictly newer)
counted_by_bang_newermt one_sec_before: 1   (expect 1)
boundary_probe: PASS — ! -newermt means mtime <= threshold midnight
duration_vs_calendar: file aged exactly 30*86400s counted_by_bang_newermt=0
  (0 means calendar method is stricter than pure duration at this clock time;
   1 means the duration-aged file already sits on/before threshold midnight)
caveat: article find method uses calendar midnight, not age_seconds > 30*86400

=== CALENDAR↔DURATION DELTA (full retention root) ===
calendar_old30: 504
duration_old30: 504
both_methods: 504
calendar_only: 0
duration_only: 0
ref_calendar_epoch: 1786579200
ref_duration_epoch: 1786626963
method_skew_seconds: 47763
calendar_duration_delta: none tonight — both methods agree on this root at this clock
calendar_duration_probe: PASS

=== TOUCH↔UTIME PLANTER (shell touch -d vs os.utime) ===
touch_planter_old30: 7 of 10
utime_planter_old30: 7 of 10
ages_days: 28 29 30 31 32 33 40 44 45 50
threshold_30d: 2026-08-13
touch_utime_planter: PASS — find counts agree (7)

=== TZ DIVERGENCE PROBE (multi-zone calendar cut) ===
tz_utc_threshold: 2026-08-13 counted=0
tz_la_threshold: 2026-08-13 counted=0
tz_tokyo_threshold: 2026-08-13 counted=0
tz_london_threshold: 2026-08-13 counted=0
tz_local_threshold: 2026-08-13
tz_divergence: none at this clock (all four thresholds: 2026-08-13); still document TZ with live figures
tz_probe: PASS (informational; does not fail cold_verify)

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
control_note: no settings file → default 30-day cleanup applies per Claude Code docs.
control_watched_red: PASS

=== ANTI-CONFLATION (wrong object must not look like retention) ===
wrote 2721 records into /tmp/transcripto-cold-final3/wrong-object-authorship-gate/retention-gate.jsonl
wrong_object_files: 1
wrong_object_records: 2721
wrong_object_old30_files: 0
anti_conflation: PASS — 2721 records in 1 file ≠ 2721 files (retention object)

=== PRODUCT BOUNDARY (transcripto has no file-age retention command) ===
product_boundary: PASS — CLI help has no file-age retention verb
help_exit: 0

=== STATS NEAR-MISS (message counts ≠ file-age) ===
stats_exit: 0
stats_home: /tmp/transcripto-cold-final3/fake-home-stats (isolated; does not touch ~/.trace)
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
PRIVACY OK: 0 hits in 218 tracked files
privacy on real tree: PASS
PRIVACY OK: 0 hits in 218 tracked files
privacy_HEAD_extract_exit: 0
privacy_HEAD_vs_worktree: PASS — git archive of HEAD is clean
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
work dir kept: /tmp/transcripto-cold-final3
```

## Embarrassment hunt (watched, not narrated)

| control | tonight |
|---------|---------|
| empty-index privacy | watched RED (exit 1); main formerly green on 0/0 |
| empty `grep -q` / `grep -qv` | both exit 1 on empty input |
| death-rate laundering | +75 old / +153 total → FORBIDDEN as deaths |
| frozen-quote reconcile | FAIL-TO-RECONCILE |
| symlink inflation | DETECTED (2 vs 1) |
| stats near-miss | DETECTED (`2,721 of the 2,721 messages`) |
| product boundary | no `retention` CLI; exit 2 |
| naive find vs transcripto | naive wins file-age |
| TZ divergence | none at this clock (all four = 2026-08-13); still publish TZ |
| calendar↔duration | fixture agree; boundary duration file counted=0 |
| independent oracle | PASS (seed 20260912 → old30=83 old45=39) |
| negative planter | 503/2720 watched RED |
| HEAD archive privacy | PASS (catches worktree-scrub / HEAD-leak trap) |
| docs defaults | cleanupPeriodDays=30; desktop=0 no age limit |

## Live re-derive (Oscar machine only)

```sh
ROOT="$HOME/.claude/projects"
echo "TZ=$(date +%Z)"
find "$ROOT" -type f -name '*.jsonl' | wc -l
find "$ROOT" -type f -name '*.jsonl' ! -newermt "$(date -d '30 days ago' +%Y-%m-%d)" | wc -l
```

Compare to frozen 504/2721 and 579/2874. Do not invent a daily death rate.
Name calendar vs duration if you switch methods. Desktop/Cowork files may be
immortal under default `desktopSessionCleanupPeriodDays=0` (OQ-4).
