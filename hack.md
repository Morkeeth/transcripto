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

1. **Slice 1 — cold stranger at the file object.** DONE.
   Ran `bash scripts/cold_verify.sh` → `cold_verify: PASS`,
   `ratio_30d: 504 of 2721`. Artifact: `docs/COLD-VERIFY-2026-08-30.md`.
2. **Slice 2 — STEP 3 ruling at the README object.** DONE.
   `docs/STEP-3-README-BELOEVED-RULING.md` recommends KEEP L66–88;
   checklist boxes unchecked for Oscar.
3. **Slice 3 — STEP 0 logged.** DONE.
   `./test_small_n.sh` and `bash scripts/test_small_n.sh` → 7/7 in checklist footer.
4. **Slice 4 — baseline arm.** DONE.
   `docs/BASELINE-ARM.md` — naive `find` wins retention; gate 8 vs naive 12.

## NOW

Done. Slices 1–4 shipped. Oscar morning clicks: STEP 3 KEEP/TRIM, live
`find` re-derive, article/X/PyPI.

## LOG

- 2026-09-05 start: no `hack.md`, no `docs/`, no `scripts/` on main.
- START one-liner: `bash scripts/test_small_n.sh` → missing; wrapper added.
- `./test_small_n.sh` → **7/7 green**.
- Baseline probe: naive `type:user`=12, coach `human_turns`=8 on fixtures-coach.
- Embarrassment: `test_privacy.sh` on empty `git init` was exit 0 → fixed to exit 1.
- `python3 -m venv` needed `apt install python3.12-venv`.
- README object: author worst-prompt gone; invented demo at L66–88. STEP 3 = KEEP.
- Official docs: `cleanupPeriodDays` default 30; separate Desktop key exists.
- Slice 1: `bash scripts/cold_verify.sh` → **cold_verify: PASS**,
  `ratio_30d: 504 of 2721`, old45=0. Artifact: `docs/COLD-VERIFY-2026-08-30.md`.
- Slice 2: `docs/STEP-3-README-BELOEVED-RULING.md` + checklist STEP 3 unchecked.
- Slice 3: 7/7 logged in checklist footer.
- Slice 4: `docs/BASELINE-ARM.md` — naive `find` wins retention simplicity.
- Stranger cold clone of this branch → `bash scripts/cold_verify.sh` → PASS.
- CI `tests` on branch: success (Python 3.9 + 3.13).
- PyPI JSON re-derived: **0.2.0** live (no bump performed).
- PR create requires Oscar approval in Cursor settings (branch is pushed).
