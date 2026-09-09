# hack.md — Transcripto night wave 2026-09-09

## NORTH STAR

A stranger cold-clones or git-archives this repo, runs one shell command with
no key and no Oscar corpus, and re-derives the **file-age** retention method
behind "504 of 2,721 files older than 30 days" — with controls that can go
RED, a baseline arm that can beat us, and a STEP 3 README ruling ready for
Oscar's morning tick.

## PROMISE LINE

**GET:** `bash scripts/cold_verify.sh` exits 0; captured output lives in
`docs/COLD-VERIFY-2026-08-30.md`; `docs/ARTICLE-01-SHIP-CHECKLIST.md` is ready
for Oscar to tick STEP 3 and the ship clicks.

**CONSTRAINT:** No outward acts (no article post, no X, no PyPI bump, no
publish). A checkbox is truth only when its done-when was RUN. Branch push +
draft PR for Oscar review is the handoff, not a public post.

## OPEN QUESTIONS

- **OQ-1 (non-blocking):** Oscar's live 504/2721 on `~/.claude/projects` cannot
  be re-derived on a cloud VM with no corpus. Ship the method + an
  arithmetic-faithful fixture + an independent find↔stat oracle + a negative
  planter that must go RED; Oscar re-runs `find` on his machine tomorrow.
- **OQ-2 (blocking for ship surface):** KEEP vs trim the README launch example.
  Cloud prepares the ruling with tonight's line refs; **Oscar ticks**. Do not
  guess the tick.
- **OQ-3 (Oscar only):** Article post · X post · PyPI publish. Agent does not.

## CONSTITUTION

1. Run it; do not read it. Tick only after the done-when command executed.
2. Re-derive every number at its object. Never carry figures from this prompt
   or from an older doc into a live claim.
3. Open the bigger object. 504/2721 is **file retention by mtime** under a
   projects root (`find … ! -newermt`), **not** an authorship-gate count of
   human turns, and **not** `stats` message counts. Do not conflate.
4. A control that has not been watched going RED is not a control. Empty-input
   greens are bugs.
5. No outward acts. Branch push + draft PR for Oscar review is allowed; public
   post/publish/PyPI is not.
6. Do not reorganise, rename, or start a new project.
7. A fixture that plants N and asserts N only proves the planter. Method truth
   requires an independent oracle that does not share the planted target, plus
   a negative planter that must FAIL.
8. Cold stranger means: after source install, retention + oracle + suites must
   PASS with no network. Docs/PyPI probes are separate and may use network;
   their absence must not paint retention green-by-skip.
9. A stranger path that only works with `.git` present is not fully cold —
   archive extracts must be exercised.
10. Prior night-wave branches are the floor, not the plan. Re-run tonight;
    do not copy old PASS lines as evidence. Main still lacks docs/scripts —
    that gap is tonight's object, not a reason to paste yesterday's artifact.

## PLAN (risk first)

1. **Slice 1 — cold stranger at the file object + RED controls.** DONE.
   Ran `bash scripts/cold_verify.sh` → `cold_verify: PASS`, `offline_core: PASS`,
   `ratio_30d: 504 of 2721`, `independent_oracle: PASS` (88/45), 
   `negative_planter: PASS`, `tz_divergence: OBSERVED`, `stats_near_miss: DETECTED`.
   Archive + wheel strangers PASS. Artifact: `docs/COLD-VERIFY-2026-08-30.md`.
   CI docs pipefail found and fixed (file-then-awk).
2. **Slice 2 — STEP 3 ruling at the README object.** DONE.
   `nl -ba README.md | sed -n '64,88p'` → invented demo L66–88;
   `docs/STEP-3-README-BELOEVED-RULING.md` recommends KEEP; checklist unchecked.
3. **Slice 3 — STEP 0 logged.** DONE.
   `./test_small_n.sh` and `bash scripts/test_small_n.sh` → 7/7 in checklist footer.
4. **Slice 4 — baseline arm that can embarrass us.** DONE.
   `docs/BASELINE-ARM.md` + `bash scripts/pip_only_baseline.sh` — naive `find`
   wins retention; pip-only `retention` exit 2; `stats` 2721/2721 near-miss
   DETECTED; gate 8 vs naive 12; wheel cwd-shadow DETECTED.

## NOW

Done. Slices 1–4 shipped. Oscar morning clicks: STEP 3 KEEP/TRIM, live
`find` re-derive (with TZ), article/X/PyPI.

## LOG

- 2026-09-09 start: main has no `hack.md`, no `docs/`, no `scripts/`. Prior
  night-wave remotes (`cold-verify-9e69`, `fed8`, `launch-7ea8`, `caf5`) are
  the floor — treated as evidence of what was attempted, **not** tonight's
  PASS. This wave must re-run at the object.
- START prep: `git fetch origin main` ok; `python3-venv` missing →
  `apt install python3-venv`; `./test_small_n.sh` → **7/7 green** (ran at
  `/workspace/test_small_n.sh`; `scripts/` did not exist yet).
- Embarrassment at start (main): empty `git init` + `test_privacy.sh` →
  printed `PRIVACY OK: 0 hits in 0 tracked files` and exited **0**.
- No live `~/.claude/projects` (OQ-1).
- PyPI JSON re-derived at start: **0.2.0**.
- Unit tests at start: **73 OK**.
- Docs object at start (`curl` settings-reference.md):
  `cleanupPeriodDays` Default **30**;
  `desktopSessionCleanupPeriodDays` Default **0** (no age limit).
- TZ tonight: host `UTC`; `date -d '30 days ago'` → `2026-08-10` (UTC) vs
  `2026-08-09` (America/Los_Angeles).
- README object opened: invented demo at L66–88; `rg` for old author-prompt
  markers → 0 hits.
- hack.md written before any product/scripts code; committed; pushed.
- Slice 1: privacy fail-closed; `scripts/cold_verify.sh` with offline core,
  oracle (seed 20260909), negative planter, boundary, TZ, stats near-miss,
  product boundary. `bash scripts/cold_verify.sh` → **PASS**.
- Archive stranger: `bash scripts/archive_stranger.sh` → **PASS**.
- Wheel stranger first run **FAIL**ed on cwd shadow (`import` bound
  `/workspace/transcripto.py` after wheel install). Trap made explicit;
  clean-cwd path → **PASS**. New embarrassment beyond prior waves.
- Slice 2: README L66–88 invented demo; KEEP ruling; Oscar ticks open.
- Slice 3: both small-n paths **7/7**; logged in checklist footer.
- Slice 4: `pip_only_baseline.sh` → find wins; pip-only `retention` exit 2;
  `stats` prints 2721/2721 typed on retention fixture (near-miss DETECTED).
- Unit tests: **73 OK**.
- CI tip `738e9d7`: test 3.9 + 3.13 **success**; cold-verify **failure** on
  `printf | awk` Broken pipe under pipefail when parsing settings-reference.
  Fixed to file-then-awk; re-ran cold_verify → **PASS**.
- README Development: stranger one-liner for `bash scripts/cold_verify.sh`.
- Added `test_privacy_empty_index.sh` to the main test matrix so the
  empty-index green-on-outage trap is caught without waiting for cold-verify.
  Ran → `privacy_empty_index_watched_red: PASS`.
- GitHub Actions on tip `619f364`: test 3.9 + 3.13 + cold-verify all
  **success**. Intermediate `738e9d7` was the only RED (docs pipefail).
