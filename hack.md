# hack.md — Transcripto night wave 2026-09-14

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
  planter that must go RED; Oscar re-runs `find` on his machine tomorrow
  (publish TZ; refuse invented death rate; name calendar vs duration; do not
  substitute `-mtime +30`).
- **OQ-2 (blocking for ship surface):** KEEP vs trim the README launch example.
  Cloud prepares the ruling with tonight's line refs; **Oscar ticks**. Do not
  guess the tick.
- **OQ-3 (Oscar only):** Article post · X post · PyPI publish. Agent does not.
- **OQ-4 (non-blocking, article honesty):** Desktop/Cowork transcripts under the
  same projects root inherit `desktopSessionCleanupPeriodDays` Default `0`
  (no age limit) per tonight's docs object. Live CLI vs Desktop mix on Oscar's
  machine is not knowable here.

## CONSTITUTION

1. Run it; do not read it. Tick only after the done-when command executed.
2. Re-derive every number at its object. Never carry figures from this prompt
   or from an older doc into a live claim.
3. Open the bigger object. 504/2721 is **file retention by mtime** under a
   projects root (`find … ! -newermt`), **not** an authorship-gate count of
   human turns, and **not** `stats` message counts. Do not conflate.
4. A control that has not been watched going RED is not a control. Empty-input
   greens are bugs. `grep -q` / `grep -qv` on empty input is not a pass.
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
    do not copy old PASS lines as evidence. Main still lacked docs/scripts at
    start — that gap was tonight's object, not a reason to paste yesterday's
    artifact.
11. Ambition beyond the floor must be able to embarrass us: naive `find`
    winning retention, `-mtime +30` looking like the article cut, `stats`
    near-miss looking like retention, empty-index privacy going green on
    outage, frozen quotes that do not reconcile, wheel cwd-shadow binding the
    tree, TZ pair traps, calendar↔duration cut deltas, touch↔utime planter
    disagreement, symlink inflation, hardlink name≠inode, death-rate
    laundering of two stamps, HEAD-archive privacy while worktree looks clean
    — all must be watched, not narrated.

## PLAN (risk first)

1. **Slice 1 — cold stranger at the file object + RED controls.** DONE.
   Ran `TRANSCRIPTO_COLD_DIR=/tmp/transcripto-cold-20260914 bash scripts/cold_verify.sh`
   → `cold_verify: PASS`, `offline_core: PASS`, `ratio_30d: 504 of 2721`,
   `independent_oracle: PASS` (93/51, seed 20260914), `negative_planter: PASS`,
   `mtime_vs_newermt: DETECTED` (6/10), `hardlink_inflation: DETECTED`,
   `symlink_inflation: DETECTED`, `tz_divergence: OBSERVED`,
   `tz_pair_trap: DETECTED` (UTC↔Tokyo agree, LA differs),
   `frozen_quote_reconcile: FAIL-TO-RECONCILE`, `stats_near_miss: DETECTED`,
   `death_rate_impossible: PASS`, `empty_grep_control: PASS`,
   `privacy_HEAD_vs_worktree: PASS`. Archive + wheel strangers PASS.
   Artifact: `docs/COLD-VERIFY-2026-08-30.md`.
2. **Slice 2 — STEP 3 ruling at the README object.** DONE.
   `nl -ba README.md | sed -n '64,90p'` → invented demo L66–88;
   `docs/STEP-3-README-BELOEVED-RULING.md` recommends KEEP; checklist unchecked.
3. **Slice 3 — STEP 0 logged.** DONE.
   `./test_small_n.sh` and `bash scripts/test_small_n.sh` → 7/7 in checklist footer.
4. **Slice 4 — baseline arm that can embarrass us.** DONE.
   `docs/BASELINE-ARM.md` + `bash scripts/pip_only_baseline.sh` — naive `find`
   wins retention; `-mtime +30` disagrees with article cut; pip-only
   `retention` exit 2; `stats` 2721/2721 near-miss DETECTED; gate 8 vs naive 12;
   wheel cwd-shadow DETECTED; hardlink inflation DETECTED.

## NOW

Done. Slices 1–4 shipped. Oscar morning clicks: STEP 3 KEEP/TRIM, live
`find` re-derive (with TZ; no invented death rate; no `-mtime +30`; name
Desktop mix), article/X/PyPI.

## LOG

- 2026-09-14 ~00:06 UTC start: main tip `fa15f1b`. No `hack.md`, no `docs/`,
  no `scripts/` on main. Prior remotes (`night-wave-p1-cold-verify-ebe8`,
  `904c`, `910a`, `launch-*`) are the **floor** — evidence of what was
  attempted, **not** tonight's PASS. This wave re-ran at the object.
- Branch: `cursor/night-wave-p1-cold-verify-1e81`.
- START: `git pull origin main` (Already up to date). System
  `pip install -e . -q` blocked by PEP 668 (expected; cold_verify uses a
  venv). Root `./test_small_n.sh` → **7/7 green**. Unit tests → **73 OK**.
- Embarrassment at start (main, RUN): empty `git init` + copy of
  `test_privacy.sh` → printed `PRIVACY OK: 0 hits in 0 tracked files` and
  exited **0**. Fixed fail-closed tonight.
- `grep -q` / `grep -qv` on empty input → exit **1** (confirmed).
- README object opened: invented demo at L66–88.
- No live `~/.claude/projects` (OQ-1).
- PyPI JSON re-derived: **0.2.0**.
- Docs object (`curl` settings-reference.md): `cleanupPeriodDays` Default
  **30**; `desktopSessionCleanupPeriodDays` Default **0** (no age limit).
- Host `TZ=UTC`. Installed `python3.12-venv`.
- Beyond-floor probe (RUN, before shipping): hours_ago 721–740 show
  `! -newermt`=1 and `-mtime +30`=0 — substitute trap is real tonight.
- Hardlink probe (RUN): `-type f`=2, unique inodes=1.
- hack.md written before any product/scripts code; committed; pushed.
- Slice 1: privacy fail-closed; `scripts/cold_verify.sh` with offline core,
  oracle (seed 20260914 → 93/51), negative planter, death-rate, empty-grep,
  symlink + hardlink inflation, mtime+n vs calendar, boundary, multi-TZ,
  frozen-quote, calendar↔duration, touch↔utime, stats near-miss, product
  boundary, HEAD-archive privacy. `bash scripts/cold_verify.sh` → **PASS**.
- Archive stranger: **PASS**. Wheel stranger: **PASS** (cwd-shadow DETECTED).
- Slice 2: README L66–88 invented demo; KEEP ruling; Oscar ticks open.
- Slice 3: both small-n paths **7/7**; logged in checklist footer.
- Slice 4: `pip_only_baseline.sh` → find wins; pip-only `retention` exit 2;
  `stats` prints 2721/2721 typed on retention fixture (near-miss DETECTED).
- Beyond floor vs prior waves: `-mtime +30` disagreement hunt + hardlink
  name≠inode inflation (ebe8 had symlink + calendar↔duration + HEAD privacy).
- Unit tests: **73 OK**. Empty-index gate in matrix via
  `test_privacy_empty_index.sh`.
- TZ tonight: divergence OBSERVED (LA differs). Pair trap: UTC↔Tokyo hide
  Pacific divergence.
