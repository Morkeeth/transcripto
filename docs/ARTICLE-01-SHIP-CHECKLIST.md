# ARTICLE-01 ship checklist — Oscar morning

**Status:** PyPI **0.2.0 live** (re-derived `curl …/pypi/transcripto/json`) ·
cold verify green 2026-09-12 ~13:11Z · article / X = **Oscar clicks only**

Agent does not post, publish, or bump PyPI.

## Pre-flight (agent ran; evidence in docs)

| gate | command | result |
|------|---------|--------|
| STEP 0 small-n | `./test_small_n.sh` | **7/7 green** (also `bash scripts/test_small_n.sh`) |
| Cold stranger | `bash scripts/cold_verify.sh` | **PASS** — see footer / `docs/COLD-VERIFY-2026-08-30.md` |
| Archive stranger | `bash scripts/archive_stranger.sh` | re-run after scripts committed (footer) |
| Wheel stranger | `bash scripts/wheel_stranger.sh` | **PASS** — `cwd_shadow_trap: DETECTED`; fixture 504/2721 PASS |
| Cold artifact | `docs/COLD-VERIFY-2026-08-30.md` | captured command output (2026-09-12 ~13:11Z) |
| Baseline arm | `docs/BASELINE-ARM.md` + `bash scripts/pip_only_baseline.sh` | naive `find` wins retention; pip-only cannot answer file-age |
| STEP 3 ruling | `docs/STEP-3-README-BELOEVED-RULING.md` | KEEP invented demo at README L66–88 |
| Privacy | `./test_privacy.sh` + `./test_privacy_empty_index.sh` | OK on real tree; empty-index exits **1** (watched RED; in matrix) |
| Suites inside cold_verify | coach/codex/cost/label_bands/small_n/cursor_partial/correction/version | all green |
| Unit tests | `python3 -m unittest discover -s tests -v` | **73 OK** |
| Docs default | curl settings-reference.md | `cleanupPeriodDays` Default **30**; desktop Default **0** |
| PyPI | `curl -sL https://pypi.org/pypi/transcripto/json` | **0.2.0** |

## STEP 3 — README launch example

See `docs/STEP-3-README-BELOEVED-RULING.md`.

Current object is the **invented** `replay --demo` block (`README.md:66–88`).
Author worst-prompt text is absent (scrubbed). Cloud recommendation: **KEEP**.

- [ ] **Oscar:** keep invented replay demo (`README.md:66–88`) — recommended
- [ ] **Oscar:** or trim the demo further

## Ship sequence (Oscar only — do not agent-click)

1. [ ] Re-derive live retention on Oscar's machine (optional but honest):
   `find ~/.claude/projects -type f -name '*.jsonl' ! -newermt "$(date -d '30 days ago' +%Y-%m-%d)" | wc -l`
   and total `find … -type f -name '*.jsonl' | wc -l`. Print `TZ=$(date +%Z)`.
   Compare to frozen 504/2721 and 579/2874. **Do not invent a daily death rate**
   (stamps FAIL-TO-RECONCILE). Name calendar vs duration if you switch methods.
   Check Desktop/Cowork mix (default desktop cleanup = 0 / no age limit).
2. [ ] Tick STEP 3 KEEP or TRIM above.
3. [ ] Post article 01 from the fleet-ops draft (path on Oscar's machine).
4. [ ] Post X / launch note.
5. [ ] PyPI publish only if a new version is intentionally cut (current source is 0.2.0).

## Footer — night wave 2026-09-12 log

```
$ ./test_small_n.sh
… 7/7 green.

$ bash scripts/test_small_n.sh
… 7/7 green.

$ TRANSCRIPTO_COLD_DIR=/tmp/transcripto-cold-tonight bash scripts/cold_verify.sh
… ratio_30d: 504 of 2721
… ASSERT fixture 504 of 2721 (old45=0): PASS
… death_rate_impossible: PASS (laundered 75 FORBIDDEN)
… empty_grep_control: PASS (-q and -qv both exit 1 on empty)
… symlink_inflation: DETECTED (name=2 type_f=1)
… negative_plant: 503 of 2720
… negative_planter: PASS
… independent_oracle: PASS (old30=83, old45=39; seed 20260912)
… boundary_probe: PASS
… duration_vs_calendar: … counted_by_bang_newermt=0
… calendar_duration_delta: none tonight (fixture ages 31–44d; skew ~47478s)
… touch_utime_planter: PASS (7 of 10)
… tz_divergence: none at this clock (all four 2026-08-13)
… frozen_quote_reconcile: FAIL-TO-RECONCILE
… product_boundary: PASS
… stats_near_miss: DETECTED
… offline_core: PASS
… docs_cleanupPeriodDays_default_30: PASS
… docs_desktop_default_0_no_age_limit: PASS
… anti_conflation: PASS — 2721 records in 1 file ≠ 2721 files
… naive type:user count: 12
… transcripto human_turns (gated): 8
… privacy_empty_index_exit: 1
… cold_verify: PASS

$ bash scripts/wheel_stranger.sh
… cwd_shadow_trap: DETECTED
… import_source: wheel site-packages OK
… ratio_30d: 504 of 2721
… product_boundary_wheel: PASS
… stats_near_miss: DETECTED on wheel arm
… wheel_stranger: PASS

$ bash scripts/pip_only_baseline.sh
… naive_find_ratio: 504 of 2721
… transcripto_retention_exit: 2
… stats_near_miss: DETECTED on pip-only arm
… pip_only_human_turns: 8
… pip_only_baseline: PASS

$ python3 -m unittest discover -s tests -v
… Ran 73 tests … OK

$ ./test_privacy_empty_index.sh
… privacy_empty_index_exit: 1
… privacy_empty_index_watched_red: PASS

$ # archive_stranger: FAIL before scripts committed (git archive empty of
$ #   scripts/). Re-run after commit; update this footer with PASS + tip SHA.
```

Not done (by design): article post · X post · PyPI bump · publish.
