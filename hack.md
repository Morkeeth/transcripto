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

1. **Slice 1 — cold stranger at the file object + RED controls.** NOW.
   Risk: planter/assert is circular; empty-index privacy greens on main;
   clone-only "stranger" misses archive extracts; calendar `find` ≠ duration;
   `stats` can launder 2721 as retention. Ship `scripts/cold_verify.sh` with
   offline core, independent oracle, negative planter, boundary/TZ probes,
   anti-conflation, product boundary, stats near-miss, privacy fail-closed,
   plus archive stranger. Artifact: `docs/COLD-VERIFY-2026-08-30.md`.
2. **Slice 2 — STEP 3 ruling at the README object.**
   Open `README.md` line refs tonight; write KEEP/TRIM recommendation;
   Oscar ticks. No code change for KEEP.
3. **Slice 3 — STEP 0 logged.**
   Re-run `./test_small_n.sh` and `bash scripts/test_small_n.sh` → 7/7;
   log commands in checklist footer.
4. **Slice 4 — baseline arm that can embarrass us.**
   Document naive `find` / pip-only vs transcripto. Honest if naive wins
   retention. `docs/BASELINE-ARM.md` + `scripts/pip_only_baseline.sh`.

## NOW

**Slice 1** — cold stranger path + RED controls + COLD-VERIFY artifact.
(hack.md exists; no product code until this file landed.)

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
  markers → 0 hits. STEP 3 ruling deferred to Slice 2 (Oscar ticks).
- hack.md written before any product/scripts code; this commit is Slice 0.
