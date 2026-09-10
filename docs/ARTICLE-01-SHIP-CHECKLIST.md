# ARTICLE-01 ship checklist — Oscar morning

**Status:** PyPI **0.2.0 live** (re-derived `curl …/pypi/transcripto/json`) ·
cold verify green 2026-09-10 · article / X = **Oscar clicks only**

Agent does not post, publish, or bump PyPI.

## Pre-flight (agent ran; evidence in docs)

| gate | command | result |
|------|---------|--------|
| STEP 0 small-n | `./test_small_n.sh` | **7/7 green** (also `bash scripts/test_small_n.sh`) |
| Cold stranger | `bash scripts/cold_verify.sh` | **PASS** — `ratio_30d: 504 of 2721`, `death_rate_impossible: PASS`, `empty_grep_control: PASS`, `independent_oracle: PASS` (96/45), `negative_planter: PASS`, `boundary_probe: PASS`, `offline_core: PASS`, `stats_near_miss: DETECTED`, docs sweep-lag + desktop immortal, `pypi_package_audit: PASS` |
| Cold artifact | `docs/COLD-VERIFY-2026-08-30.md` | captured command output |
| Archive stranger | `bash scripts/archive_stranger.sh` | **PASS** (`archive_has_git: no`) |
| Wheel stranger | `bash scripts/wheel_stranger.sh` | **PASS** (`cwd_shadow_trap: DETECTED`) |
| Baseline arm | `docs/BASELINE-ARM.md` + `bash scripts/pip_only_baseline.sh` | naive `find` wins retention; pip-only `retention` exit 2; gate 8 vs naive 12; stats near-miss DETECTED |
| STEP 3 ruling | `docs/STEP-3-README-BELOEVED-RULING.md` | KEEP invented demo at README L66–88 |
| Privacy | `./test_privacy.sh` | OK on real tree; empty-index exits **1** (`./test_privacy_empty_index.sh`) |
| Suites inside cold_verify | coach/codex/cost/label_bands/small_n/cursor_partial/correction/version | all green |
| Docs default | curl settings-reference.md | `cleanupPeriodDays` Default **30**; desktop Default **0**; background sweep after session start |
| PyPI | `curl -sL https://pypi.org/pypi/transcripto/json` | **0.2.0**; wheel has **no** cold_verify |
| Unit tests | `python3 -m unittest discover -s tests -v` | **73 OK** |

## STEP 3 — README launch example

See `docs/STEP-3-README-BELOEVED-RULING.md`.

Current object is the **invented** `replay --demo` block (`README.md:66–88`).
Author worst-prompt text is absent (scrubbed). Cloud recommendation: **KEEP**.

- [ ] **Oscar:** keep invented replay demo (`README.md:66–88`) — recommended
- [ ] **Oscar:** or trim the demo further

## Ship sequence (Oscar only — do not agent-click)

1. [ ] Re-derive live retention on Oscar's machine (optional but honest):
   `find ~/.claude/projects -name '*.jsonl' ! -newermt "$(date -d '30 days ago' +%Y-%m-%d)" | wc -l`
   and total `find … | wc -l`. Publish **TZ**. Compare to frozen 504/2721 and 579/2874.
   Do **not** print (579−504)=75 as a daily death rate (total rose).
2. [ ] Check CLI vs Desktop mix before claiming universal 30-day deletion
   (docs: Desktop default 0 = no age limit; deletion is a post-session sweep).
3. [ ] Tick STEP 3 KEEP or TRIM above.
4. [ ] Post article 01 from the fleet-ops draft (path on Oscar's machine).
5. [ ] Post X / launch note.
6. [ ] PyPI publish only if a new version is intentionally cut (current source is 0.2.0).

## Footer — night wave 2026-09-10 log

```
$ ./test_small_n.sh
… 7/7 green.

$ bash scripts/test_small_n.sh
… 7/7 green.

$ bash scripts/cold_verify.sh
… ratio_30d: 504 of 2721
… ASSERT fixture 504 of 2721 (old45=0): PASS
… death_rate_impossible: PASS — total rose and old30 rose; refuse daily death rate
… empty_grep_control: PASS
… negative_planter: PASS — watched RED (wrong plant does not satisfy 504/2721)
… independent_oracle: PASS  (python/find old30=96, old45=45)
… boundary_probe: PASS
… duration_vs_calendar: … counted_by_bang_newermt=0
… stats_near_miss: DETECTED — 2,721 of the 2,721 messages … 100.0%
… docs_cleanupPeriodDays_default_30: PASS
… docs_desktop_default_0_no_age_limit: PASS
… docs_sweep_lag: PASS
… docs_desktop_immortal_default: PASS
… pypi_package_audit: PASS — published wheel has no cold_verify script
… offline_core: PASS
… cold_verify: PASS

$ bash scripts/archive_stranger.sh
… archive_has_git: no
… cold_verify: PASS

$ bash scripts/wheel_stranger.sh
… cwd_shadow_trap: DETECTED
… wheel_stranger: PASS

$ bash scripts/pip_only_baseline.sh
… naive_find_ratio: 504 of 2721
… transcripto_retention_exit: 2
… naive_type_user: 12 / pip_only_human_turns: 8
… pip_only_baseline: PASS

$ ./test_privacy_empty_index.sh
… privacy_empty_index_watched_red: PASS

$ python3 -m unittest discover -s tests -v
… Ran 73 tests … OK

$ git clone --depth 1 --branch cursor/night-wave-p1-launch-fcb9 \
    https://github.com/Morkeeth/transcripto.git /tmp/transcripto-stranger-clone
$ cd /tmp/transcripto-stranger-clone && bash scripts/cold_verify.sh
… cold_verify: PASS
```

Not done (by design): article post · X post · PyPI bump · publish.
