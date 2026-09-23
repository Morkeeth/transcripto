# ARTICLE-01 ship checklist — Oscar morning

**Status:** PyPI **0.2.0 live** (re-derived `curl …/pypi/transcripto/json`) ·
cold verify green 2026-09-23 · article / X = **Oscar clicks only**

Agent does not post, publish, or bump PyPI.

## Pre-flight (agent ran; evidence in docs)

| gate | command | result |
|------|---------|--------|
| STEP 0 small-n | `./test_small_n.sh` | **7/7 green** (also `bash scripts/test_small_n.sh`) |
| Cold stranger | `bash scripts/cold_verify.sh` | **PASS** — `ratio_30d: 504 of 2721`, `death_rate_impossible: PASS`, `empty_grep_control: PASS`, `independent_oracle: PASS` (94/46, seed 20260923), `negative_planter: PASS`, `hardlink_inode_inflation: DETECTED`, `tz_pair_trap: DETECTED`, `boundary_probe: PASS`, `offline_core: PASS`, `stats_near_miss: DETECTED`, tip caveat PRESENT / published ABSENT, docs dual-gate, `published_verb_gap: DETECTED` |
| Cold artifact | `docs/COLD-VERIFY-2026-08-30.md` | captured command output (ANSI stripped) |
| Archive stranger | `bash scripts/archive_stranger.sh` | **PASS** (`archive_has_git: no`) |
| Wheel stranger | `bash scripts/wheel_stranger.sh` | **PASS** (`cwd_shadow_trap: DETECTED`) |
| Cold clone | `bash scripts/cold_clone_stranger.sh` | **PASS** (clone ≠ worktree) |
| Baseline arm | `docs/BASELINE-ARM.md` + `bash scripts/pip_only_baseline.sh` | naive `find` wins retention; pip-only `retention` exit 2; gate 8 vs naive 12; stats near-miss DETECTED; verb gap DETECTED |
| STEP 3 ruling | `docs/STEP-3-README-BELOEVED-RULING.md` | KEEP invented demo at README L132–154 |
| Privacy | `./test_privacy.sh` | OK on real tree; empty-index exits **1** (`./test_privacy_empty_index.sh`) |
| Suites inside cold_verify | coach/codex/cost/label_bands/small_n/cursor_partial/correction/version | all green |
| Docs default | curl settings-reference.md | `cleanupPeriodDays` Default **30**; desktop Default **0**; dual-gate DETECTED |
| PyPI | `curl -sL https://pypi.org/pypi/transcripto/json` | **0.2.0**; wheel has **no** cold_verify; stranger verbs **ABSENT** |
| Unit tests | `python3 -m unittest discover -s tests -q` | **94 OK** |

## STEP 3 — README launch example

See `docs/STEP-3-README-BELOEVED-RULING.md`.

Current object is the **invented** `replay --demo` block (`README.md:132–154`).
Author worst-prompt text is absent (scrubbed). Cloud recommendation: **KEEP**.

- [ ] **Oscar:** keep invented replay demo (`README.md:132–154`) — recommended
- [ ] **Oscar:** or trim the demo further

## Ship sequence (Oscar only — do not agent-click)

1. [ ] Re-derive live retention on Oscar's machine (optional but honest):
   `find ~/.claude/projects -type f -name '*.jsonl' ! -newermt "$(date -d '30 days ago' +%Y-%m-%d)" | wc -l`
   and total `find … -type f -name '*.jsonl' | wc -l`. Publish **TZ**. Compare to frozen 504/2721 and 579/2874.
   Do **not** print (579−504)=75 as a daily death rate (total rose).
   Name whether the quote is **paths** or **inodes** (tonight: hardlink path count ≠ inode count).
2. [ ] Check CLI vs Desktop mix before claiming universal 30-day deletion
   (docs tonight: Desktop default 0 = no age limit; dual-gate with `cleanupPeriodDays`;
   deletion is a post-session sweep; managed `cleanupPeriodDays` ignores Desktop key).
3. [ ] Tick STEP 3 KEEP or TRIM above.
4. [ ] Post article 01 from the fleet-ops draft (path on Oscar's machine).
5. [ ] Post X / launch note.
6. [ ] PyPI publish only if a new version is intentionally cut (current source is 0.2.0;
   tip has stranger verbs + stats caveat that live 0.2.0 lacks).

## Footer — night wave 2026-09-23 log (branch 15b6)

```
$ ./test_small_n.sh
… 7/7 green.

$ bash scripts/test_small_n.sh
… 7/7 green.

$ TRANSCRIPTO_COLD_DIR=/tmp/transcripto-cold-tonight-15b6 bash scripts/cold_verify.sh
… ratio_30d: 504 of 2721
… ASSERT fixture 504 of 2721 (old45=0): PASS
… death_rate_impossible: PASS — total rose and old30 rose; refuse daily death rate
… empty_grep_control: PASS
… blank_line_wc_trap: DETECTED
… symlink_inflation: DETECTED
… hardlink_inode_inflation: DETECTED — -type f counted 2 paths / 1 inode
… negative_planter: PASS — watched RED (wrong plant does not satisfy 504/2721)
… independent_oracle: PASS  (python/find old30=94, old45=46; seed 20260923)
… boundary_probe: PASS
… calendar_duration_delta: none tonight
… tz_divergence: OBSERVED — 2 distinct calendar cuts; pair trap UTC↔Tokyo vs LA
… stats_near_miss: DETECTED — 2,721 of the 2,721 messages … 100.0%
… stats_anti_conflation_caveat: PASS (tip)
… published_stats_caveat: ABSENT (live 0.2.0)
… published_verb_gap: DETECTED
… docs_cleanupPeriodDays_default_30: PASS
… docs_desktop_default_0_no_age_limit: PASS
… docs_desktop_dual_gate: DETECTED
… stranger_product_journey: PASS
… offline_core: PASS
… cold_verify: PASS

$ bash scripts/archive_stranger.sh
… archive_has_git: no · cold_verify: PASS

$ bash scripts/wheel_stranger.sh
… cwd_shadow_trap: DETECTED · wheel_stranger: PASS

$ bash scripts/cold_clone_stranger.sh
… clone_ne_worktree: PASS · cold_verify: PASS

$ bash scripts/pip_only_baseline.sh
… naive_find_ratio: 504 of 2721
… arm_a_ruling: naive find WINS retention
… arm_b_ruling: naive wins simplicity; pip-only gate 8 < 12
… pip_only_baseline: PASS

$ ./test_privacy_empty_index.sh
… privacy_empty_index_watched_red: PASS (exit 1)

$ python3 -m unittest discover -s tests -q
… Ran 94 tests … OK
```
