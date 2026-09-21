# Cold verify — 2026-08-30 artifact (re-run 2026-09-21, branch 8b78)

**One command (cold stranger, no key, no Oscar corpus):**

```sh
bash scripts/cold_verify.sh
```

**Prerequisite on Debian/Ubuntu cloud images:** `python3-venv`
(`sudo apt install python3.12-venv`) **or** `virtualenv` on `PATH`.
Without one of those, `python3 -m venv` fails (ensurepip missing). Tonight
this host had no ensurepip; cold_verify fell back to `virtualenv` and
recorded `venv_partial_without_pip: DETECTED`. System `pip install -e .`
may also fail under PEP 668; the script uses its own venv.

**Archive stranger (no `.git`):**

```sh
bash scripts/archive_stranger.sh
```

**Wheel stranger (local wheel, offline install, clean cwd):**

```sh
bash scripts/wheel_stranger.sh
```

**Cold clone stranger (fresh clone of this tip, ≠ worktree):**

```sh
bash scripts/cold_clone_stranger.sh
```

## What this verifies

The **file-age method** behind the retention story:

```sh
ROOT=~/.claude/projects   # or the generated fixture on a cloud VM
THIRTY=$(date -d '30 days ago' +%Y-%m-%d)
TOTAL=$(find "$ROOT" -type f -name '*.jsonl' | wc -l)
OLD30=$(find "$ROOT" -type f -name '*.jsonl' ! -newermt "$THIRTY" | wc -l)
echo "$OLD30 of $TOTAL older than 30d (as of $THIRTY)"
```

**Object:** jsonl **files** under a projects root, aged by mtime.
Always `-type f` (symlink inflation watched: name-only find double-counts).
**Not** an authorship-gate count of human turns. **Not** `transcripto stats`
message counts (tonight tip `stats` on the retention fixture printed
`2,721 of the 2,721 messages … 100.0%` **and** named the object; published
0.2.0 prints the near-miss **without** the caveat — embarrassment).

Frozen Oscar quotes (machine-local; **not** re-derived on this VM):

| stamp | figure | note |
|-------|--------|------|
| 2026-08-28 | 504 of 2,721 | weekly review freeze |
| 2026-08-29 | 579 of 2,874 | same `find` method next day |

The two stamps do not reconcile by arithmetic. Delta old30 = **+75**, delta
total = **+153**. Total rose, so this is not a deletion day. No daily death
rate is claimed; tonight's `death_rate_impossible` control refuses the
laundered figure **75**. `frozen_quote_reconcile: FAIL-TO-RECONCILE`.

The sharper companion fact on Oscar's machine was `older_than_45d == 0` —
deletion already happened; it is not a future risk only.

When `~/.claude/projects` is absent, the script generates an
**arithmetic-faithful fixture**: 2721 files, 504 touched to ages 31–44 days
(so the 45-day count stays 0), and asserts exact equality. A **negative
planter** (503 of 2720) must fail that assert. An **independent oracle**
(180 blind ages, seed from tonight's UTC date) compares find ↔ Python mtime
without sharing the 504/2721 target.

## Docs object (re-derived tonight)

`curl` → `https://code.claude.com/docs/en/settings-reference.md`
(fetched 2026-09-21T12:15Z; sections `cleanupPeriodDays` /
`desktopSessionCleanupPeriodDays`):

- `cleanupPeriodDays` **Default: `30`**. Deletion is a **background sweep
  after a session starts** (not continuous). Setting `0` fails validation.
- `desktopSessionCleanupPeriodDays` **Default: `0`**, which sets **no age
  limit**. Without the key, Desktop/Cowork transcripts are kept at any age.
- Dual-gate: Claude Code deletes a Desktop transcript once it is older than
  **both** this limit and `cleanupPeriodDays`. With Desktop default `0` and
  CLI default `30`, Desktop sessions are **not** age-deleted by the CLI timer
  alone. When managed settings set `cleanupPeriodDays`, that period applies
  and the Desktop key is ignored.
- Do not flatten "30-day deletion" onto a mixed CLI/Desktop projects root
  without checking the live mix (OQ-4).

## Captured output

Command run tonight: `bash scripts/cold_verify.sh` (exit 0).
Work dir: `/tmp/cold-verify-out` (kept via `TRANSCRIPTO_COLD_DIR`).
Branch tip at capture: `bf9b3de` on `cursor/night-wave-p1-launch-8b78`.
ANSI colour codes stripped for the artifact.

```text
=== COLD VERIFY · 2026-09-21T12:13:54Z ===
repo: /workspace
work: /tmp/cold-verify-out

venv_stdlib_exit: 1
venv_partial_without_pip: DETECTED — stdlib venv exit 1 left python without pip
venv_green_without_pip: adjacent — nonzero exit but partial tree looks usable
venv_stdlib: FAIL (exit 1) — see ensurepip / python3-venv
The virtual environment was not created successfully because ensurepip is not
available.  On Debian/Ubuntu systems, you need to install the python3-venv
package using the following command.

    apt install python3.12-venv
venv_backend: virtualenv-fallback (ensurepip outage watched)
venv_pip_ok: 26.2.1 py 3.12.3
transcripto: transcripto 0.2.0

=== OFFLINE CORE (proxies poisoned to 127.0.0.1:9) ===

generating fixture: 2721 jsonl files (504 aged 31–44d)…
fixture_files_written: 2721 old_planted: 504
retention source: FIXTURE /tmp/cold-verify-out/fixtures-retention-504-of-2721
  (no live ~/.claude/projects on this machine — method + arithmetic only)

=== RETENTION (find method, re-derived) ===
mode: fixture
as_of: 2026-09-21T12:14:01Z
threshold_30d: mtime <= 2026-08-22
threshold_45d: mtime <= 2026-08-07
total_jsonl: 2721
older_than_30d: 504
older_than_45d: 0
ratio_30d: 504 of 2721
oldest_file: /tmp/cold-verify-out/fixtures-retention-504-of-2721/demo-project/sessions/session-0055.jsonl
oldest_mtime: 2026-08-08T12:13:57Z

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
blank_line_wc_l: 1  (expect 1 — invents a file)
empty_string_wc_l: 0  (expect 0)
blank_line_wc_trap: DETECTED — never trust wc -l of an empty file list

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
oracle_seed: 20260921
oracle_files: 180
oracle_age_days_min_max: 0 60
oracle_python_old30: 87
oracle_find_old30: 87
oracle_python_old45: 40
oracle_find_old45: 40
threshold_30d_epoch: 1787356800.0
threshold_45d_epoch: 1786060800.0
independent_oracle: PASS
(seed Random(20260921) from UTC date — not the retention quote; collision guard active)

=== BOUNDARY PROBE (exactly at threshold) ===
threshold_midnight_epoch: 1787356800 (2026-08-22 00:00:00 local)
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
ref_calendar_epoch: 1787356800
ref_duration_epoch: 1787400842
method_skew_seconds: 44042
calendar_duration_delta: none tonight — both methods agree on this root at this clock
calendar_duration_probe: PASS

=== TOUCH↔UTIME PLANTER (shell touch -d vs os.utime) ===
touch_planter_old30: 7 of 10
utime_planter_old30: 7 of 10
ages_days: 28 29 30 31 32 33 40 44 45 50
threshold_30d: 2026-08-22
touch_utime_planter: PASS — find counts agree (7)

=== TZ DIVERGENCE PROBE (multi-zone calendar cut) ===
tz_utc_threshold: 2026-08-22 counted=0
tz_la_threshold: 2026-08-22 counted=0
tz_tokyo_threshold: 2026-08-22 counted=0
tz_london_threshold: 2026-08-22 counted=0
tz_local_threshold: 2026-08-22
tz_divergence: none at this clock (all four thresholds: 2026-08-22); still document TZ with live figures
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
wrote 2721 records into /tmp/cold-verify-out/wrong-object-authorship-gate/retention-gate.jsonl
wrong_object_files: 1
wrong_object_records: 2721
wrong_object_old30_files: 0
anti_conflation: PASS — 2721 records in 1 file ≠ 2721 files (retention object)

=== PRODUCT BOUNDARY (transcripto has no file-age retention command) ===
product_boundary: PASS — CLI help has no file-age retention verb
help_exit: 0

=== STRANGER PRODUCT JOURNEY (import-example → ask → changes → handoff) ===
stranger_journey_exit: 0
stranger_journey_home: /tmp/cold-verify-out/stranger-home
stranger_ask_open_count: 3
stranger_brief_ok: 1
stranger_handoff_mode: 600
  
  Status: acknowledgement pending. No receiver agent was invoked by this command.
  
  Evidence: source available; Open command below reopens the exact request.
  
  Prepared instruction for receiver: No, use 30 seconds instead for the forecast cache; upstream data changes twice a minute.
  
  Previous request: Set the forecast cache timeout to 60 seconds in config/cache.toml.
  
  Source: /tmp/cold-verify-out/stranger-home/.transcripto/imports/claude/public-change-example.jsonl:L4
  
  Open: transcripto replay /tmp/cold-verify-out/stranger-home/.transcripto/imports/claude/public-change-example.jsonl --line 4
  
  Recorded follow-up (tool execution, not task correctness):
  - edit config/cache.toml (succeeded)
  
  Still missing before completion can be claimed:
  - receiver acknowledgement
  - task correctness verification
  
stranger_product_journey: PASS

=== STATS NEAR-MISS (message counts ≠ file-age) ===
stats_exit: 0
stats_home: /tmp/cold-verify-out/fake-home-stats (isolated; does not touch ~/.trace)
stats_out:
2,721 of the 2,721 messages in your index are things you typed.  100.0%
the rest is the machine answering. `coach` counts raw transcript records instead
  of indexed messages, so its share is smaller; same numerator, wider population.
These are indexed message counts, not transcript file ages. File retention is a find/mtime question, not this command.

where you typed them

files your prompts moved most
stats_near_miss: DETECTED — stats output contains 2721 (retention denominator lookalike)
stats_near_miss_ruling: do NOT quote stats as retention evidence
stats_anti_conflation_caveat: PASS — stats names the object (messages ≠ file ages)
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
PRIVACY OK: 0 structural hits in 33 production/doc files; credential patterns checked across 220 tracked files
privacy on real tree: PASS
PRIVACY OK: 0 structural hits in 33 production/doc files; credential patterns checked across 220 tracked files
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
docs_desktop_dual_gate: DETECTED — Desktop age requires both limits; Default 0 alone is incomplete
docs_desktop_dual_gate_probe: PASS
docs_desktop_setting_present: PASS

=== FIND|HEAD SIGPIPE TRAP (pipefail ≠ missing files) ===
find_head_pipefail_exit: 0
find_head_sigpipe_trap: DETECTED — exit 0 under pipefail; do not treat as missing files
find_head_sigpipe_ruling: retention counts use find|wc -l, never find|head
find_head_sigpipe_probe: PASS
pypi_transcripto_version: 0.2.0 (re-derived)
wheel_file_count: 9
pypi_wheel_cold_verify_entries: 0
pypi_wheel_local_name: transcripto-0.2.0-py3-none-any.whl
pypi_package_audit: PASS — published wheel has 0 cold_verify entries; pip-only cannot ship stranger retention

=== PUBLISHED STATS CAVEAT GAP (PyPI wheel vs tip) ===
published_stats_exit: 0
published_stats_head:
2,721 of the 2,721 messages in your index are things you typed.  100.0%
the rest is the machine answering. `coach` counts raw transcript records instead
  of indexed messages, so its share is smaller; same numerator, wider population.

published_stats_caveat: ABSENT — live 0.2.0 wheel lacks tip anti-conflation caveat
published_stats_caveat_ruling: embarrassment — pip-only stats can still look like retention
published_stats_caveat_probe: PASS (gap watched; tip repair is this branch)
tip_stats_caveat: PRESENT

=== PUBLISHED VERB GAP (PyPI wheel vs tip stranger flow) ===
published_module_file: /tmp/cold-verify-out/pypi-stats-venv/lib/python3.12/site-packages/transcripto.py
published_module_cwd_shadow: no
published_parsers: index,watch,ask,search,find,trace,sessions,stats,cost,coach,export-run,replay
published_stranger_verbs_missing: import-example,changes,handoff,receive-handoff,import-lab,quickstart
published_verb_gap: DETECTED — pip-only missing import-example,changes,handoff,receive-handoff,import-lab,quickstart; README stranger flow needs source/tip
published_verb_gap_probe: PASS (gap watched; not a cold_verify fail)
tip_parsers_stranger: import-example,changes,handoff,receive-handoff,import-lab,quickstart
tip_stranger_verbs_missing: (none)
tip_stranger_verbs: PRESENT

cold_verify: PASS
work dir kept: /tmp/cold-verify-out
```

## Sister arms (also RUN tonight)

| arm | command | result |
|-----|---------|--------|
| Archive stranger | `bash scripts/archive_stranger.sh` | **PASS** (`archive_has_git: no`) |
| Wheel stranger | `bash scripts/wheel_stranger.sh` | **PASS** (`cwd_shadow_trap: DETECTED`) |
| Cold clone | `bash scripts/cold_clone_stranger.sh` | **PASS** (`clone_ne_worktree`) |
| Pip-only baseline | `bash scripts/pip_only_baseline.sh` | **PASS** — naive find wins retention |

## Tonight vs prior floor (honest deltas)

Prior wave `cursor/night-wave-p1-launch-0583` recorded TZ divergence
(LA `2026-08-21` vs UTC/Tokyo/London `2026-08-22`). Tonight at
`2026-09-21T12:14Z` all four zones agreed on threshold `2026-08-22`
(`tz_divergence: none`). Calendar↔duration also agreed on the full fixture
(`calendar_only: 0`, `duration_only: 0`). Same controls, different clock —
publish **TZ** with any live figure; do not copy a prior wave's divergence
line as tonight's evidence.

Oracle tonight (seed `20260921`): old30=**87**, old45=**40** — re-derived,
not carried from the floor's PASS line (same seed happens to match because
UTC date is unchanged).

## What this does not prove

- Oscar's live 504/2721 on `~/.claude/projects` (absent on this VM).
- That transcripto products answer file-age (it does not; naive `find` wins).
- That published PyPI 0.2.0 ships this script or the tip stranger verbs
  (wheel audit: 0 cold_verify entries; verb gap DETECTED).
