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
   greens are bugs. (Main's `test_privacy.sh` was green on empty `git init`
   tonight — that is Slice 1 risk.)
5. No outward acts. Branch push + draft PR for Oscar review is allowed; public
   post/publish/PyPI is not.
6. Do not reorganise, rename, or start a new project.
7. A fixture that plants N and asserts N only proves the planter. Method truth
   requires an independent oracle that does not share the planted target.
8. Cold stranger means: after source install, retention + oracle + suites must
   PASS with no network. Docs/PyPI probes are separate and may use network;
   their absence must not paint retention green-by-skip.

## PLAN (risk first)

1. **Slice 1 — cold stranger at the file object + controls that can go RED.**
   Privacy empty-index fail-closed. `scripts/cold_verify.sh` with arithmetic
   fixture, independent oracle, boundary + calendar-vs-duration probes,
   anti-conflation, offline-after-install core. Artifact:
   `docs/COLD-VERIFY-2026-08-30.md`. Also: true `git archive` stranger run.
2. **Slice 2 — STEP 3 ruling at the README object.**
   Open README line refs; KEEP/TRIM recommendation; Oscar ticks.
3. **Slice 3 — STEP 0 logged.**
   Re-run `./test_small_n.sh` and `bash scripts/test_small_n.sh`; log 7/7 in
   checklist footer with the command.
4. **Slice 4 — baseline arm that can embarrass us.**
   `docs/BASELINE-ARM.md`: naive `find` vs transcripto on retention; pip-install
   only (live PyPI, no clone) vs clone path; authorship gate naive vs coach.
   Honest if naive/`find`/pip-only wins on simplicity.

## NOW

**Slice 1 only.** Write privacy fail-closed + cold_verify + capture COLD-VERIFY
doc. Do not tick Slice 2–4 until Slice 1's done-when has been RUN.

Done-when: `bash scripts/cold_verify.sh` exits 0 and
`docs/COLD-VERIFY-2026-08-30.md` contains tonight's command output including
`ratio_30d`, `independent_oracle`, and `cold_verify: PASS`.

## LOG

- 2026-09-06 start (bc-fa7a9e70): main has no `hack.md`, no `docs/`, no
  `scripts/`. Prior night-wave branches (fed8, caf5) are floor, not truth —
  this wave re-runs at the object and goes bigger (archive stranger,
  offline-after-install core, pip-only baseline).
- START: `pip install -e . -q` ok; `./test_small_n.sh` → **7/7 green**;
  `bash scripts/test_small_n.sh` → missing (no scripts/ yet).
- Embarrassment already: empty `git init` + `test_privacy.sh` → exit **0**
  (`PRIVACY OK: 0 hits in 0 tracked files`) — green-on-outage.
- No live `~/.claude/projects` (OQ-1).
- `python3 -m venv` needed `apt install python3.12-venv` (was missing).
- PyPI JSON re-derived: **0.2.0**.
- Docs object opened (`settings-reference.md`): `cleanupPeriodDays` Default
  **30**; `desktopSessionCleanupPeriodDays` Default **0** (no age limit).
- hack.md written before any code.
