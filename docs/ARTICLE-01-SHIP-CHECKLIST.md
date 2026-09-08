# ARTICLE-01 ship checklist — Oscar morning

**Status:** PyPI **0.2.0 live** (re-derived `curl …/pypi/transcripto/json`) ·
cold verify green 2026-09-08 · article / X = **Oscar clicks only**

Agent does not post, publish, or bump PyPI.

## Pre-flight (agent ran; evidence in docs)

| gate | command | result |
|------|---------|--------|
| STEP 0 small-n | `./test_small_n.sh` | **7/7 green** (also `bash scripts/test_small_n.sh`) |
| Cold stranger | `bash scripts/cold_verify.sh` | **PASS** — `ratio_30d: 504 of 2721`, `independent_oracle: PASS`, `negative_planter: PASS`, `boundary_probe: PASS`, `offline_core: PASS`, `tz_divergence: OBSERVED`, `stats_near_miss: DETECTED`, old45=0 |
| Archive stranger | `bash scripts/archive_stranger.sh` | **PASS** (no `.git`; ephemeral privacy index) |
| Cold artifact | `docs/COLD-VERIFY-2026-08-30.md` | captured command output |
| Baseline arm | `docs/BASELINE-ARM.md` + `bash scripts/pip_only_baseline.sh` | naive `find` wins retention; pip-only cannot answer file-age; gate 8 vs naive 12 |
| STEP 3 ruling | `docs/STEP-3-README-BELOEVED-RULING.md` | KEEP invented demo at README L66–88 |
| Privacy | `./test_privacy.sh` | OK on real tree; empty-index exits **1** (watched RED) |
| Suites inside cold_verify | coach/codex/cost/label_bands/small_n/cursor_partial/correction/version | all green |
| Unit tests | `python3 -m unittest discover -s tests -v` | **73 OK** |
| CI cold-verify job | `.github/workflows/tests.yml` job `cold-verify` | added; runs `bash scripts/cold_verify.sh` on push/PR |
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
   `find ~/.claude/projects -name '*.jsonl' ! -newermt "$(date -d '30 days ago' +%Y-%m-%d)" | wc -l`
   and total `find … | wc -l`. Print `TZ=$(date +%Z)`. Compare to frozen
   504/2721 and 579/2874.
2. [ ] Tick STEP 3 KEEP or TRIM above.
3. [ ] Post article 01 from the fleet-ops draft (path on Oscar's machine).
4. [ ] Post X / launch note.
5. [ ] PyPI publish only if a new version is intentionally cut (current source is 0.2.0).

## Footer — night wave 2026-09-08 log

```
$ ./test_small_n.sh
… 7/7 green.

$ bash scripts/test_small_n.sh
… 7/7 green.

$ bash scripts/cold_verify.sh
… ratio_30d: 504 of 2721
… ASSERT fixture 504 of 2721 (old45=0): PASS
… negative_plant: 503 of 2720
… negative_planter: PASS
… independent_oracle: PASS
… boundary_probe: PASS
… duration_vs_calendar: … counted_by_bang_newermt=0
… tz_divergence: OBSERVED (UTC 2026-08-09 vs LA 2026-08-08)
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

$ bash scripts/archive_stranger.sh
… archive_has_git: no
… privacy_mode: archive-extract …
… cold_verify: PASS

$ bash scripts/pip_only_baseline.sh
… naive_find_ratio: 504 of 2721
… transcripto_retention_exit: 2
… stats_near_miss: DETECTED on pip-only arm
… pip_only_human_turns: 8
… pip_only_baseline: PASS

$ python3 -m unittest discover -s tests -v
… Ran 73 tests … OK

$ # GitHub Actions on e450282 (after privacy scrub)
… test (3.9): success · test (3.13): success · cold-verify: success
```

Not done (by design): article post · X post · PyPI bump · publish.
