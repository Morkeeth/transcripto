# hack.md — Transcripto night wave 2026-09-12

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
  (publish TZ; refuse invented death rate; name calendar vs duration).
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
    do not copy old PASS lines as evidence. Main still lacks docs/scripts —
    that gap is tonight's object, not a reason to paste yesterday's artifact.
11. Ambition beyond the floor must be able to embarrass us: naive `find`
    winning retention, `stats` near-miss looking like retention, empty-index
    privacy going green on outage, frozen quotes that do not reconcile, wheel
    cwd-shadow binding the tree, TZ pair traps (including inverse pairs),
    calendar↔duration count deltas, touch↔utime planter disagreement,
    symlink inflation of `find` totals, death-rate laundering of two stamps,
    HEAD-archive privacy while worktree looks clean — all must be watched,
    not narrated.

## PLAN (risk first)

1. **Slice 1 — cold stranger at the file object + RED controls.** DONE.
   Ran `TRANSCRIPTO_COLD_DIR=/tmp/transcripto-cold-final3 bash scripts/cold_verify.sh`
   → `cold_verify: PASS`, `offline_core: PASS`, `ratio_30d: 504 of 2721`,
   `independent_oracle: PASS` (83/39, seed 20260912), `negative_planter: PASS`,
   `death_rate_impossible: PASS`, `empty_grep_control: PASS` (-q and -qv),
   `symlink_inflation: DETECTED`, `tz_divergence: none` (all four 2026-08-13),
   `frozen_quote_reconcile: FAIL-TO-RECONCILE`, `stats_near_miss: DETECTED`,
   `calendar_duration_delta: none` on fixture / boundary counted=0,
   `touch_utime_planter: PASS` (7/10), `privacy_HEAD_vs_worktree: PASS`.
   Archive + wheel strangers PASS. Artifact: `docs/COLD-VERIFY-2026-08-30.md`.
   Tip `34ab34a` archive re-run PASS.
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
`find` re-derive (with TZ; no invented death rate; name calendar vs duration;
Desktop mix), article/X/PyPI.

## LOG

- 2026-09-12 ~13:07 UTC start: main tip `fa15f1b`. No `hack.md`, no `docs/`,
  no `scripts/`. Prior remotes (`night-wave-p1-cold-verify-910a`,
  `night-wave-p1-launch-fcb9`, `cold-verify-904c`, …) are the **floor** —
  evidence of what was attempted, **not** tonight's PASS. This wave re-runs
  at the object.
- Branch: `cursor/night-wave-p1-cold-verify-ebe8`.
- START: `git pull origin main` (Already up to date). System
  `pip install -e . -q` wrote to `~/.local` (PATH warning). Root
  `./test_small_n.sh` → **7/7 green**. Unit tests → **73 OK**.
- Embarrassment at start (main, RUN): empty `git init` + copy of
  `test_privacy.sh` → printed `PRIVACY OK: 0 hits in 0 tracked files` and
  exited **0**. Fixed fail-closed tonight.
- `grep -qv` on empty input → exit **1** (confirmed). `grep -q` on empty →
  exit **1**.
- README object opened: invented demo at L66–88
  (`nl -ba README.md | sed -n '64,90p'`). Author worst-prompt fragment absent
  from README (privacy guard still watches the guarded phrases).
- No live `~/.claude/projects` (OQ-1).
- PyPI JSON re-derived: **0.2.0**.
- CLI object: no `retention` subcommand.
- Docs object (`curl` settings-reference.md): `cleanupPeriodDays` Default
  **30**; `desktopSessionCleanupPeriodDays` Default **0** (no age limit).
- Host `TZ=UTC`. Installed `python3.12-venv`.
- Symlink probe (RUN): name-only=2, `-type f`=1.
- hack.md written before any product/scripts code; committed; pushed.
- Slice 1: privacy fail-closed; `scripts/cold_verify.sh` with offline core,
  oracle (seed 20260912 → 83/39), negative planter, death-rate, empty-grep
  -q/-qv, symlink inflation, boundary, multi-TZ, frozen-quote, calendar↔
  duration, touch↔utime, stats near-miss, product boundary, HEAD-archive
  privacy. `bash scripts/cold_verify.sh` → **PASS**.
- Intermediate FAIL (RUN): first archive stranger after docs commit failed —
  STEP-3 ruling quoted a privacy-guarded fragment while worktree privacy
  looked green. Scrubbed; added HEAD-archive privacy control; archive
  re-run → **PASS** (tip `34ab34a`).
- Archive stranger: **PASS**. Wheel stranger: **PASS** (cwd-shadow DETECTED).
- Slice 2: README L66–88 invented demo; KEEP ruling; Oscar ticks open.
- Slice 3: both small-n paths **7/7**; logged in checklist footer.
- Slice 4: `pip_only_baseline.sh` → find wins; pip-only `retention` exit 2;
  `stats` prints 2721/2721 typed on retention fixture (near-miss DETECTED).
- Beyond floor vs prior waves: symlink `-type f` trap + `grep -qv` empty
  control + HEAD-archive privacy (caught tonight's real leak) + death-rate
  merged from fcb9 into the 910a floor.
- Unit tests: **73 OK**. Empty-index gate in matrix via
  `test_privacy_empty_index.sh`.
- TZ tonight: no divergence (all four zones `2026-08-13`). Still publish TZ
  with live figures — absence of divergence is clock-local.
- GitHub Actions tip `7a17de3` (run 34696040300): test 3.9 + 3.13 + cold-verify all **success**.
