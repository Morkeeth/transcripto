# hack.md — Transcripto night wave 2026-09-05

## NORTH STAR

A stranger cold-clones this repo, runs one shell command with no key and no
Oscar corpus, and re-derives the **file-age** retention method behind
"504 of 2,721 files older than 30 days" — plus STEP 0, a baseline arm, and a
STEP 3 README ruling ready for Oscar's morning tick.

## PROMISE LINE

**GET:** `bash scripts/cold_verify.sh` exits 0; its captured output lives in
`docs/COLD-VERIFY-2026-08-30.md`; `docs/ARTICLE-01-SHIP-CHECKLIST.md` is ready
for Oscar to tick STEP 3 and the ship clicks.

**CONSTRAINT:** No outward acts (no article post, no X, no PyPI bump, no
publish). A checkbox is truth only when its done-when was RUN.

## OPEN QUESTIONS

- **OQ-1 (non-blocking):** Oscar's live 504/2721 on `~/.claude/projects` cannot
  be re-derived on a cloud VM. Ship the method + an arithmetic-faithful
  fixture; Oscar re-runs `find` on his machine tomorrow.
- **OQ-2 (blocking for ship surface):** KEEP vs trim the README launch example.
  Cloud prepares the ruling; **Oscar ticks**. Do not guess the tick.
- **OQ-3 (Oscar only):** Article post · X post · PyPI publish. Agent does not.

## CONSTITUTION

1. Run it; do not read it. Tick only after the done-when command executed.
2. Re-derive every number at its object. Never carry figures from this prompt
   or from an older doc.
3. Open the bigger object. 504/2721 is **file retention by mtime** under a
   projects root (`find … ! -newermt`), **not** an authorship-gate count of
   human turns. Do not conflate the two.
4. A control that has not been watched going RED is not a control. Empty-input
   greens are bugs.
5. No outward acts. Branch push + draft PR for Oscar review is allowed; public
   post/publish/PyPI is not.
6. Do not reorganise, rename, or start a new project.
7. Privacy stays green on the real tree; the privacy guard itself must fail
   closed on an empty index.

## PLAN (risk first)

1. **Slice 1 — cold stranger at the file object.** `scripts/cold_verify.sh`
   builds a 2721-file fixture with 504 aged 31–44 days, asserts
   `504 of 2721` and `older_than_45d == 0`, runs STEP 0 + baseline + suites.
   Capture output into `docs/COLD-VERIFY-2026-08-30.md`.
   Done-when: `bash scripts/cold_verify.sh` → `cold_verify: PASS` and the
   captured doc contains the ratio line.
2. **Slice 2 — STEP 3 ruling at the README object.** Open current README lines;
   recommend KEEP/trim with line refs; Oscar ticks tomorrow.
   Done-when: `docs/STEP-3-README-BELOEVED-RULING.md` exists; checklist STEP 3
   boxes are unchecked for Oscar.
3. **Slice 3 — STEP 0 logged.** Re-run `./test_small_n.sh` (and scripts
   wrapper); log 7/7 in checklist footer with the command.
   Done-when: footer cites the command and the observed `7/7 green`.
4. **Slice 4 — baseline arm.** Document naive `find` / naive `type:user` vs
   transcripto; honest if naive wins on simplicity for the retention claim.
   Done-when: `docs/BASELINE-ARM.md` exists with numbers re-derived tonight.

## NOW

Slice 1 — write and run `scripts/cold_verify.sh`; capture cold verify doc.

## LOG

- 2026-09-05 start: no `hack.md`, no `docs/`, no `scripts/` on main.
- START one-liner: `bash scripts/test_small_n.sh` → missing (expected).
- `./test_small_n.sh` → **7/7 green** (command run).
- Baseline probe on `fixtures-coach`: naive `type:user`=12, coach
  `human_turns`=8 (re-derived).
- Embarrassment: `test_privacy.sh` on empty `git init` → **PRIVACY OK: 0 hits
  in 0 tracked files, exit 0** — false green. Fix in Slice 1.
- `python3 -m venv` failed until `apt install python3.12-venv`.
- README object: beloeved author prompt is gone; replay demo at L66–88 is
  invented. STEP 3 ruling must cite the current object, not stale L79–81.
- Official Claude Code sessions docs: `cleanupPeriodDays` default 30;
  separate `desktopSessionCleanupPeriodDays` for Desktop/Cowork.
- This file created. Code work begins only after this commit.
