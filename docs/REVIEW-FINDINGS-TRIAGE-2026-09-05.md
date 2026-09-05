# REVIEW-FINDINGS-TRIAGE · 2026-09-05

Triage against **current tip** `81a0986` (`feat/instant-replay` / this branch base), not against cloud `main` alone.

**Objects measured tonight**

| Object | Ref / id | SCHEMA | Modules |
|---|---|---|---|
| Cloud `main` | `fa15f1b` | 3 | 3 (`transcripto`, `_core`, `_replay`) |
| Oscar tip (`feat/instant-replay`) | `81a0986` (+8 ahead of main, 0 behind) | 7 | 7 (+ sources, evidence, continuity, coaching) |
| Live PyPI | `transcripto==0.2.0` wheel sha256 `530a5d3c…` | 3 | 3 |
| Overnight cold-verify branch | `cursor/night-wave-p1-cold-verify-fed8` @ `1121014` | n/a (docs/scripts on top of main) | privacy empty-index fix present |

`git rev-list --left-right --count origin/main...origin/feat/instant-replay` → `0 8`.

No uncommitted Oscar-disk deltas were visible in this cloud checkout (clean tree at tip). Divergence is **branch tip vs main vs PyPI**, not a dirty working tree.

No dedicated prior `REVIEW-FINDINGS-*.md` existed on any remote branch. Findings below are reconstructed from: PR #1 claim of adversarial review (Fable / Cursor / separate reviewer — issues said fixed at merge), overnight cold-verify / PyPI / trace-analysis agent receipts, then **re-run at this tip**.

Status vocabulary: **fixed** · **still open** · **not reproducible** · **documented / deferred** · **blocked (Oscar object)** · **fixed tonight**.

---

## A. Embarrassing / launch-blocking (measured tonight)

### F1 · Version label collision: tip and PyPI both claim `0.2.0`, different objects
- **Status:** still open (Oscar publish tick; no bump/publish tonight)
- **Evidence:** `bash scripts/check_installed_package.sh` → `version_schema_collision True` (tip SCHEMA 7 vs wheel SCHEMA 3). Clean-room `pip install --no-cache-dir transcripto==0.2.0` from `/tmp` → schema 3, no `transcripto_sources`. Tip wheel → schema 7 + four extra modules.
- **Why it matters:** `READ-CONTRACT.md` on tip documents `transcripto.ask/1`, packets, schema-7 columns. Live PyPI `ask` rejects `--json` (`unrecognized arguments: --json`). A stranger following tip docs with `uvx --from transcripto==0.2.0` does not get the tip contract.

### F2 · Privacy guard green on empty git index
- **Status:** fixed tonight
- **Was:** `git init` + `bash test_privacy.sh` → `PRIVACY OK: 0 hits in 0 tracked files` exit 0
- **Now:** same command → `PRIVACY FAIL: git ls-files returned 0 files…` exit 1. Real tree still green: `bash test_privacy.sh` → OK.
- **Ported from:** `origin/cursor/night-wave-p1-cold-verify-fed8` (was not on tip/main).

### F3 · README install-pin / `should print` soft-only in `test_version.sh`
- **Status:** fixed tonight
- **Was:** mismatched README versions only WARN.
- **Now:** `transcripto==X` and `should print **X**` hard-fail. Control watched RED: temporarily pin `0.1.3` → exit 1; restore → exit 0.

---

## B. Consumer / installed-package path

### F4 · Consumer integration (READ-CONTRACT on tip wheel)
- **Status:** fixed / verified tonight (tip only)
- **Command:** `bash scripts/check_consumer_integration.sh`
- **Result:** PASS — `user_version 7`, schema-7 `v_messages` columns present, `transcripto.ask/1`, `transcripto.packet/1` freshness `current`, `transcripto.coaching-snapshot/1` + comparison.

### F5 · Naive / published baseline loses tip consumer contract
- **Status:** documented (embarrassing; expected until publish)
- **Command:** clean-room PyPI venv → `select session_file,source_line,record_sha256 from v_messages` → `OperationalError: no such column: session_file` (exit 1). Tip script PASS.
- **Finding:** the alternative any stranger installs today cannot satisfy tip READ-CONTRACT.

### F6 · Live PyPI wheel longdesc gate
- **Status:** not reproducible as RED on current 0.2.0
- **Command:** `bash scripts/check_installed_package.sh` → `pypi_longdesc_gate green` (pins all `0.2.0`, wheel VERSION `0.2.0`). Historical RED was 0.1.4 package selling 0.1.3.

### F7 · `sessions` empty-index silence
- **Status:** not reproducible on tip
- **Was (PyPI cold-verify wave):** after empty index, quiet zero lines / silence risk.
- **Now:** empty HOME → `Your index is empty. \`transcripto index\` found no transcripts to read.` (exit 0). Speaks; product whether exit should be non-zero remains OQ-4.

### F8 · Path-leakage false green on installed-package import
- **Status:** fixed as procedure (logged in WRONG)
- **Was tonight:** first `pip install transcripto==0.2.0` from `/workspace` cwd imported tip modules (`transcripto_sources YES`, schema 7) — **wrong object**.
- **Correct object:** cwd `/tmp`, `PYTHONPATH` unset, `--no-cache-dir` → schema 3, modules absent.

---

## C. Trace / correction findings (prior wave; tip check)

### F9 · T1 commit-only durable in coach
- **Status:** fixed on tip (present)
- **Evidence:** coach tiers include `commit` / `COMMIT-WITNESSED` in `transcripto.py`; tip suites green (`python3 -m unittest discover -s tests` → 103 OK; shell suites 0 FAIL).

### F10 · T2 multi-harness `ROOTS`
- **Status:** fixed on tip
- **Evidence:** `ROOTS` lists Claude + Codex + Cursor; `test_replay.CLITests.test_search_automatically_indexes_all_three` OK.

### F11 · T3 same-second / ordinal timestamps
- **Status:** fixed on tip (schema 7 identity / ordinal fields present in core + views)
- **Evidence:** consumer columns `timestamp_basis` etc.; continuity/evidence tests OK. No separate `test_trace.sh` on tip (trace-wave artifact not merged).

### F12 · T4 bash redirects (`cat > file`) false “nothing durable”
- **Status:** still open / deferred
- **Evidence:** no redirect durable detection in tip sources (`rg` for redirect/`cat >` durable path empty beyond unrelated). Not fixed tonight (needs corpus frequency; out of install/triage lane).

### F13 · T5 partial Cursor tool_use coach vs trace disagree
- **Status:** documented / deferred (by design on different objects)
- **Evidence:** `test_cursor_partial.sh` 7/7 green (no invented success). Disagreement across coach/trace surfaces left as documented honesty, not a single merged verdict.

### F14 · T6 existing DB re-index after schema bump
- **Status:** still open (operator)
- **Evidence:** tip `SCHEMA_VERSION = 7`; published/local schema-3 DBs need rebuild. Tip `init_schema` rebuilds when version mismatches; operators with `~/.trace/trace.db` must run index after upgrade.

### F15 · T7 `export-run latest` empty HOME exit 2
- **Status:** not reproducible as a bug (intentional)
- **Command:** empty HOME → exit 2, `no transcript matches 'latest'`.

### F16 · Correction v2 opt-in / live P/R
- **Status:** still open on tip / blocked
- **Evidence:** tip `_CORRECTION_VERSION` allows only `v0`/`v1` (default v1). Trace-wave v2 not on this tip. Live P/R blocked (OQ-1, no Oscar corpus).

---

## D. Retention / article findings (overnight cold-verify; not re-theatred)

### F17 · 504/2721 wrong-object conflation (file age ≠ authorship gate)
- **Status:** documented on `fed8`; not re-run as theater tonight
- **Oscar leftover:** live `find` re-derive on machine with `~/.claude/projects`.

### F18 · Desktop/Cowork separate retention key
- **Status:** still open (OQ-3) — Desktop default not opened tonight.

### F19 · Privacy empty-index + cold-verify scripts on `fed8` only
- **Status:** privacy empty-index **ported tonight**; full `scripts/cold_verify.sh` retention pack **not** merged (would redo overnight theater / expand scope into article lane).

---

## E. Cost / misc

### F20 · `cost --days` mtime window vs epoch fixtures
- **Status:** not reproducible on this checkout
- **Evidence:** fixture mtimes are `2026-09-04` (clone time), not Unix epoch. `cost --root fixtures --days 3650` and `--days 0` both returned priced rows. Semantics still mtime-based in `collect_cost`; surprise remains for epoch trees / untouched archives.

---

## Commands that closed the triage loop

```sh
git rev-parse origin/main origin/feat/instant-replay
git rev-list --left-right --count origin/main...origin/feat/instant-replay
bash test_privacy.sh   # green on tip; RED on empty git init
bash test_version.sh
python3 -m unittest discover -s tests -v   # 103 OK (clean HOME)
for t in test_*.sh; do bash "$t" || exit 1; done
bash scripts/check_consumer_integration.sh
bash scripts/check_installed_package.sh
# clean-room PyPI:
cd /tmp && python3 -m venv /tmp/pypi-clean/venv
/tmp/pypi-clean/venv/bin/pip install --no-cache-dir transcripto==0.2.0
```
