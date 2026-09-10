# hack.md — Transcripto night wave 2026-09-10

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
  planter that must go RED + a death-rate impossibility control; Oscar re-runs
  `find` on his machine tomorrow (publish TZ with the figure).
- **OQ-2 (blocking for ship surface):** KEEP vs trim the README launch example.
  Cloud prepares the ruling with tonight's line refs; **Oscar ticks**. Do not
  guess the tick.
- **OQ-3 (Oscar only):** Article post · X post · PyPI publish. Agent does not.
- **OQ-4 (non-blocking, article honesty):** Do Desktop/Cowork transcripts under
  the same projects root inherit `desktopSessionCleanupPeriodDays` Default `0`
  (no age limit)? Live mix of CLI vs Desktop files on Oscar's machine is not
  knowable here. Docs object opened tonight; live split is Oscar's.

## CONSTITUTION

1. Run it; do not read it. Tick only after the done-when command executed.
2. Re-derive every number at its object. Never carry figures from this prompt
   or from an older doc into a live claim.
3. Open the bigger object. 504/2721 is **file retention by mtime** under a
   projects root (`find … ! -newermt`), **not** an authorship-gate count of
   human turns, and **not** `stats` message counts. Do not conflate.
4. A control that has not been watched going RED is not a control. Empty-input
   greens are bugs. `grep -q` on empty input is not a pass.
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
11. Two frozen stamps (504/2721 and 579/2874) must not be allowed to print a
    daily death rate. An executable control rejects that arithmetic.

## PLAN (risk first)

1. **Slice 1 — cold stranger at the file object + RED controls + death-rate
   impossibility + docs desktop caveat.** DONE.
   Ran `bash scripts/cold_verify.sh` → `cold_verify: PASS`,
   `death_rate_impossible: PASS`, `empty_grep_control: PASS`,
   `independent_oracle: PASS` (96/45), `negative_planter: PASS`,
   `offline_core: PASS`, docs sweep-lag + desktop immortal,
   `pypi_package_audit: PASS`. Artifact: `docs/COLD-VERIFY-2026-08-30.md`.
2. **Slice 2 — STEP 3 ruling at the README object.** DONE.
   `nl -ba README.md | sed -n '64,88p'` → invented demo L66–88;
   `docs/STEP-3-README-BELOEVED-RULING.md` recommends KEEP; checklist unchecked.
3. **Slice 3 — STEP 0 logged.** DONE.
   `./test_small_n.sh` and `bash scripts/test_small_n.sh` → 7/7 in checklist footer.
4. **Slice 4 — baseline arm that can embarrass us.** DONE.
   `docs/BASELINE-ARM.md` + `bash scripts/pip_only_baseline.sh` — naive `find`
   wins retention; pip-only `retention` exit 2; stats 2721/2721 near-miss
   DETECTED; gate 8 vs naive 12; archive + wheel strangers PASS;
   cwd-shadow DETECTED; PyPI wheel has no cold_verify.

## NOW

Done. Slices 1–4 shipped. Oscar morning clicks: STEP 3 KEEP/TRIM, live
`find` re-derive (with TZ + Desktop mix check), article/X/PyPI.

## LOG

- 2026-09-10 start: main has no `hack.md`, no `docs/`, no `scripts/`. Prior
  night-wave remotes (esp. `cursor/night-wave-p1-launch-83da`) are the floor —
  treated as evidence of what was attempted, **not** tonight's PASS.
- `git fetch origin main` ok; branch `cursor/night-wave-p1-launch-fcb9`.
- `python3-venv` was missing → `apt install python3.12-venv`.
- START: system `pip install -e .` blocked (PEP 668 externally-managed);
  `./test_small_n.sh` via tree `python3` → **7/7 green**.
- Unit tests at start: **73 OK**.
- PyPI JSON at start: **0.2.0**.
- Embarrassment at start (main): empty `git init` + `test_privacy.sh` →
  printed `PRIVACY OK: 0 hits in 0 tracked files` and exited **0**.
- No live `~/.claude/projects` (OQ-1).
- Docs object opened at start (`curl` settings-reference.md):
  `cleanupPeriodDays` **Default: `30`**;
  `desktopSessionCleanupPeriodDays` **Default: `0`** (no age limit);
  deletion is a **background sweep after a session starts** (not continuous).
- hack.md written before any product/scripts code; committed; pushed.
- Slice 1: privacy fail-closed; `scripts/cold_verify.sh` with offline core,
  oracle (seed 20260910), negative planter, death-rate impossibility,
  empty-grep control, boundary, TZ, stats near-miss, docs sweep-lag,
  desktop immortal, PyPI package audit. `bash scripts/cold_verify.sh` →
  **PASS** (captured in `docs/COLD-VERIFY-2026-08-30.md`).
- Oracle tonight: old30=**96**, old45=**45** (not carried from prior waves).
- Death-rate: frozen delta old +75 / total +153 → laundered "75 deaths"
  FORBIDDEN.
- Stats near-miss: `2,721 of the 2,721 messages … 100.0%` DETECTED.
- duration_vs_calendar counted_by_bang_newermt=**0** tonight.
- TZ: UTC and LA agreed on `2026-08-11` at this clock (no divergence tonight;
  still publish TZ with live figures).
- Archive stranger → **PASS**. Wheel stranger → **PASS** (cwd shadow
  DETECTED). pip-only baseline → **PASS** (naive find wins).
- Slice 2: README L66–88 invented demo; KEEP ruling; Oscar ticks open.
- Slice 3: both small-n paths **7/7**; logged in checklist footer.
- Slice 4: baseline doc + pip_only; PyPI wheel audit 0 cold_verify hits.
- Unit tests after: **73 OK**.
- README Development points at `bash scripts/cold_verify.sh`.
- `test_privacy_empty_index.sh` added to the matrix via `test_*.sh` glob.
