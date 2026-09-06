# hack.md — Transcripto night wave 2026-09-06 (bc-fa7a9e70)

## NORTH STAR

A stranger cold-clones (or git-archives) this repo, runs one shell command with
no key and no Oscar corpus, and re-derives the **file-age** retention method
behind "504 of 2,721 files older than 30 days" — with an independent oracle that
can fail us, a pip-only baseline that can beat us on simplicity, and a STEP 3
README ruling ready for Oscar's morning tick.

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
  arithmetic-faithful fixture + an independent find↔stat oracle; Oscar re-runs
  `find` on his machine tomorrow.
- **OQ-2 (blocking for ship surface):** KEEP vs trim the README launch example.
  Cloud prepares the ruling; **Oscar ticks**. Do not guess the tick.
- **OQ-3 (Oscar only):** Article post · X post · PyPI publish. Agent does not.

## CONSTITUTION

1. Run it; do not read it. Tick only after the done-when command executed.
2. Re-derive every number at its object. Never carry figures from this prompt
   or from an older doc into a live claim.
3. Open the bigger object. 504/2721 is **file retention by mtime** under a
   projects root (`find … ! -newermt`), **not** an authorship-gate count of
   human turns. Do not conflate the two.
4. A control that has not been watched going RED is not a control. Empty-input
   greens are bugs.
5. No outward acts. Branch push + draft PR for Oscar review is allowed; public
   post/publish/PyPI is not.
6. Do not reorganise, rename, or start a new project.
7. A fixture that plants N and asserts N only proves the planter. Method truth
   requires an independent oracle that does not share the planted target.
8. Cold stranger means: after source install, retention + oracle + suites must
   PASS with no network. Docs/PyPI probes are separate and may use network;
   their absence must not paint retention green-by-skip.
9. A stranger path that only works with `.git` present is not fully cold —
   archive extracts must be exercised.

## PLAN (risk first)

1. **Slice 1 — cold stranger at the file object + controls that can go RED.** DONE.
   Ran `bash scripts/cold_verify.sh` → `cold_verify: PASS`, `offline_core: PASS`,
   `ratio_30d: 504 of 2721`, `independent_oracle: PASS`. Archive stranger first
   FAIL then PASS after privacy ephemeral-index fix. Artifact:
   `docs/COLD-VERIFY-2026-08-30.md`.
2. **Slice 2 — STEP 3 ruling at the README object.** DONE.
   `docs/STEP-3-README-BELOEVED-RULING.md` recommends KEEP L66–88;
   checklist boxes unchecked for Oscar.
3. **Slice 3 — STEP 0 logged.** DONE.
   `./test_small_n.sh` and `bash scripts/test_small_n.sh` → 7/7 in checklist footer.
4. **Slice 4 — baseline arm that can embarrass us.** DONE.
   `docs/BASELINE-ARM.md` + `bash scripts/pip_only_baseline.sh` — naive `find`
   wins retention; pip-only cannot answer file-age; gate 8 vs naive 12;
   `stats` 2721/2721 near-miss documented.

## NOW

Done. Slices 1–4 shipped. Oscar morning clicks: STEP 3 KEEP/TRIM, live
`find` re-derive, article/X/PyPI.

## LOG

- 2026-09-06 start (bc-fa7a9e70): main has no `hack.md`, no `docs/`, no
  `scripts/`. Prior night-wave branches (fed8, caf5) treated as floor.
- START: `pip install -e . -q` ok; `./test_small_n.sh` → **7/7 green**;
  `bash scripts/test_small_n.sh` → missing.
- Embarrassment at start: empty `git init` + `test_privacy.sh` → exit **0**.
- No live `~/.claude/projects` (OQ-1). Needed `apt install python3.12-venv`.
- PyPI JSON re-derived: **0.2.0**. Docs object: `cleanupPeriodDays` Default
  **30**; desktop Default **0**.
- hack.md written before any code; committed; pushed.
- Slice 1: privacy fail-closed; `scripts/cold_verify.sh` with offline core,
  oracle, boundary, product boundary. `bash scripts/cold_verify.sh` → **PASS**.
- Archive stranger first run → **FAIL** (privacy needs `.git`). Fixed ephemeral
  index; re-run → **PASS**.
- Slice 2: README L66–88 invented demo; KEEP ruling; Oscar ticks open.
- Slice 3: both small-n paths **7/7**; logged in checklist footer.
- Slice 4: `pip_only_baseline.sh` → find wins; pip-only `retention` exit 2;
  `stats` prints 2721/2721 typed on retention fixture (near-miss).
- Unit tests: **73 OK**.
- PR create requires Oscar approval in Cursor settings (branch is pushed).
