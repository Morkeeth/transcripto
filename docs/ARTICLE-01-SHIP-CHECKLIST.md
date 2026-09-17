# ARTICLE-01 ship checklist — Oscar morning

**Status:** PyPI **0.2.0 live** (re-derived `curl …/pypi/transcripto/json`) ·
cold verify green 2026-09-17 ~08:19Z · article / X = **Oscar clicks only**

Agent does not post, publish, or bump PyPI.

## Pre-flight (agent ran; evidence in docs)

| gate | command | result |
|------|---------|--------|
| STEP 0 small-n | `./test_small_n.sh` | **7/7 green** (also `bash scripts/test_small_n.sh`) |
| Cold stranger | `bash scripts/cold_verify.sh` | **PASS** — see footer / `docs/COLD-VERIFY-2026-08-30.md` |
| Archive stranger | `bash scripts/archive_stranger.sh` | **PASS** |
| Wheel stranger | `bash scripts/wheel_stranger.sh` | **PASS** — `cwd_shadow_trap: DETECTED`; fixture 504/2721 PASS |
| Cold clone | `bash scripts/cold_clone_stranger.sh` | **PASS** |
| Cold artifact | `docs/COLD-VERIFY-2026-08-30.md` | captured command output (2026-09-17 ~08:19Z) |
| Baseline arm | `docs/BASELINE-ARM.md` + `bash scripts/pip_only_baseline.sh` | naive `find` wins; published verb gap DETECTED |
| STEP 3 ruling | `docs/STEP-3-README-BELOEVED-RULING.md` | KEEP invented demo at README L132–154 |
| Privacy | `./test_privacy.sh` + `./test_privacy_empty_index.sh` | OK on real tree; empty-index exits **1**; HEAD archive check in cold_verify |
| Suites inside cold_verify | coach/codex/cost/label_bands/small_n/cursor_partial/correction/version | all green |
| Unit tests | `python3 -m unittest discover -s tests -q` | **94 OK** |
| Docs default | curl settings-reference.md | `cleanupPeriodDays` Default **30**; desktop Default **0** |
| PyPI | `curl -sL https://pypi.org/pypi/transcripto/json` | **0.2.0** |
| Published gap | wheel audit inside cold_verify | stats caveat **ABSENT**; stranger verbs **missing** on 0.2.0 |
| CI | GitHub Actions tip `8ffb3c0` | test 3.9 + 3.13 + cold-verify all **success** (run 35199341649) |

## STEP 3 — README launch example

See `docs/STEP-3-README-BELOEVED-RULING.md`.

Current object is the **invented** `replay --demo` block (`README.md:132–154`).
Author worst-prompt text is absent (scrubbed). Cloud recommendation: **KEEP**.

- [ ] **Oscar:** keep invented replay demo (`README.md:132–154`) — recommended
- [ ] **Oscar:** or trim the demo further

## Ship sequence (Oscar only — do not agent-click)

1. [ ] Re-derive live retention on Oscar's machine (optional but honest):
   `find ~/.claude/projects -type f -name '*.jsonl' ! -newermt "$(date -d '30 days ago' +%Y-%m-%d)" | wc -l`
   and total `find … -type f -name '*.jsonl' | wc -l`. Print `TZ=$(date +%Z)`.
   Compare to frozen 504/2721 and 579/2874. **Do not invent a daily death rate**
   (stamps FAIL-TO-RECONCILE). Name calendar vs duration if you switch methods.
   Check Desktop/Cowork mix (default desktop cleanup = 0 / no age limit).
2. [ ] Tick STEP 3 KEEP or TRIM above.
3. [ ] Decide whether article/README stranger flow should wait on a PyPI cut that
   includes tip stranger verbs + stats caveat (tonight: **0.2.0 lacks both**),
   or point strangers at source/clone + `bash scripts/cold_verify.sh`.
4. [ ] Post article 01 from the fleet-ops draft (path on Oscar's machine).
5. [ ] Post X / launch note.
6. [ ] PyPI publish only if a new version is intentionally cut (current source is 0.2.0;
   tip has unreleased stranger verbs + stats caveat).

## Footer — night wave 2026-09-17 log

```
$ ./test_small_n.sh
… 7/7 green.

$ bash scripts/test_small_n.sh
… 7/7 green.

$ TRANSCRIPTO_COLD_DIR=/tmp/transcripto-cold-tonight bash scripts/cold_verify.sh
… venv_partial_without_pip: DETECTED
… venv_backend: virtualenv-fallback
… ratio_30d: 504 of 2721
… ASSERT fixture 504 of 2721 (old45=0): PASS
… death_rate_impossible: PASS (laundered 75 FORBIDDEN)
… empty_grep_control: PASS (-q and -qv both exit 1 on empty)
… symlink_inflation: DETECTED (name=2 type_f=1)
… negative_planter: PASS
… independent_oracle: PASS (old30=90, old45=46; seed 20260917)
… boundary_probe: PASS
… calendar_duration_delta: none tonight
… touch_utime_planter: PASS (7 of 10)
… tz_divergence: none at this clock (all four 2026-08-18)
… frozen_quote_reconcile: FAIL-TO-RECONCILE
… stranger_product_journey: PASS
… stats_near_miss: DETECTED
… stats_anti_conflation_caveat: PASS (tip)
… offline_core: PASS
… published_stats_caveat: ABSENT
… published_verb_gap: DETECTED
… tip_stranger_verbs: PRESENT
… cold_verify: PASS

$ bash scripts/archive_stranger.sh
… cold_verify: PASS

$ bash scripts/wheel_stranger.sh
… cwd_shadow_trap: DETECTED
… wheel_stranger: PASS

$ bash scripts/cold_clone_stranger.sh
… cold_verify: PASS

$ bash scripts/pip_only_baseline.sh
… naive_find_ratio: 504 of 2721
… pip_only_verb_gap: DETECTED
… arm_a_ruling: naive find WINS retention
… pip_only_baseline: PASS

$ python3 -m unittest discover -s tests -q
… Ran 94 tests … OK

$ ./test_privacy_empty_index.sh
… privacy_empty_index_watched_red: PASS
```

Not done (by design): article post · X post · PyPI bump · publish.
